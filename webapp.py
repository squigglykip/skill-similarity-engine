#!/usr/bin/env python3
"""
Skill Similarity Engine - POC Web Interface

This is a Streamlit web app that provides an interactive interface 
for exploring job similarity analysis results.
"""

import os
import sys
import glob
import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime

# Add the src directory to the Python path if not installed as a package
src_path = os.path.join(os.path.dirname(__file__), 'src')
if os.path.exists(src_path) and src_path not in sys.path:
    sys.path.insert(0, src_path)

# Set page config
st.set_page_config(
    page_title="Job Similarity Analysis POC",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply custom CSS for better appearance
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
    }
    h1, h2, h3 {
        margin-bottom: 1rem;
    }
    .metric-container {
        background-color: #f0f2f6;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Title and description
st.title("Job Similarity Analysis - POC")
st.markdown("""
This interactive dashboard allows you to explore job similarity analysis results 
from the Skill Similarity Engine POC run.
""")

# Sidebar with controls
with st.sidebar:
    st.header("Controls")
    
    # Data selection section
    st.subheader("Data Selection")
    
    # Scan for available output directories
    output_base_dir = "./data/poc/output"
    output_dirs = []
    
    if os.path.exists(output_base_dir):
        # List all poc_run directories
        output_dirs = sorted([
            d for d in os.listdir(output_base_dir) 
            if os.path.isdir(os.path.join(output_base_dir, d)) and d.startswith("poc_run_")
        ], reverse=True)  # Most recent first
    
    if not output_dirs:
        st.error("No POC run output directories found. Please run the POC first.")
        st.stop()
    
    # Select run to analyze
    selected_run = st.selectbox(
        "Select POC Run", 
        options=output_dirs,
        format_func=lambda x: f"{x.replace('poc_run_', '')} ({x})"
    )
    
    run_dir = os.path.join(output_base_dir, selected_run)
    
    # Find available departments (based on heatmap files)
    heatmap_files = glob.glob(os.path.join(run_dir, "heatmap_*.png"))
    departments = [os.path.basename(f).replace("heatmap_", "").replace(".png", "") for f in heatmap_files]
    
    if not departments:
        st.warning("No department heatmaps found in this run.")
        all_csv_files = glob.glob(os.path.join(run_dir, "*.csv"))
        if not all_csv_files:
            st.error("No data files found in this run directory.")
            st.stop()
    
    # Filter settings
    st.subheader("Filters")
    
    # Department selection
    selected_dept = st.selectbox(
        "Department", 
        options=["All Departments"] + departments if departments else ["All Departments"]
    )
    
    # Similarity threshold
    similarity_threshold = st.slider(
        "Similarity Threshold", 
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        step=0.05,
        help="Show only job pairs with similarity above this threshold"
    )
    
    # Visualization options
    st.subheader("Visualization Options")
    
    color_scheme = st.selectbox(
        "Color Scheme",
        options=["viridis", "plasma", "inferno", "magma", "cividis"]
    )
    
    # Analysis options
    st.subheader("Analysis Options")
    
    top_n_pairs = st.slider(
        "Top N Similar Job Pairs",
        min_value=5,
        max_value=50,
        value=10,
        step=5,
        help="Number of top similar job pairs to display"
    )

# Load data
try:
    # Check if there's a summary statistics file
    stats_file = os.path.join(run_dir, "summary_statistics.csv")
    has_stats = os.path.exists(stats_file)
    
    # Determine which similarity matrix to load
    if selected_dept == "All Departments":
        matrix_file = glob.glob(os.path.join(run_dir, "job_similarity_all_departments.*"))[0]
    else:
        dept_matrix_file = os.path.join(run_dir, f"similarity_matrix_{selected_dept}.csv")
        if os.path.exists(dept_matrix_file):
            matrix_file = dept_matrix_file
        else:
            # Try finding any matrix file for this department
            dept_files = glob.glob(os.path.join(run_dir, f"*{selected_dept}*.csv"))
            if dept_files:
                matrix_file = dept_files[0]
            else:
                st.error(f"No similarity matrix found for department: {selected_dept}")
                st.stop()
    
    # Load the similarity matrix
    similarity_df = pd.read_csv(matrix_file, index_col=0)
    
    # Load job metadata if available
    jobs_metadata = None
    jobs_file = glob.glob(os.path.join(run_dir, "jobs_metadata.csv"))
    if jobs_file:
        jobs_metadata = pd.read_csv(jobs_file[0])
    
    # Show a dashboard with multiple sections
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("Overview")
        
        # Show metrics
        if has_stats:
            stats_df = pd.read_csv(stats_file)
            metric_cols = st.columns(4)
            
            with metric_cols[0]:
                st.metric("Total Jobs", int(stats_df["total_jobs"].iloc[0]))
            
            with metric_cols[1]:
                st.metric("Mean Similarity", f"{stats_df['mean_similarity'].iloc[0]:.3f}")
            
            with metric_cols[2]:
                st.metric("Min Similarity", f"{stats_df['min_similarity'].iloc[0]:.3f}")
            
            with metric_cols[3]:
                st.metric("Max Similarity", f"{stats_df['max_similarity'].iloc[0]:.3f}")
        else:
            # Calculate basic stats
            total_jobs = len(similarity_df)
            mean_sim = similarity_df.values.mean()
            min_sim = similarity_df.values.min()
            max_sim = similarity_df.values.max()
            
            metric_cols = st.columns(4)
            
            with metric_cols[0]:
                st.metric("Total Jobs", total_jobs)
            
            with metric_cols[1]:
                st.metric("Mean Similarity", f"{mean_sim:.3f}")
            
            with metric_cols[2]:
                st.metric("Min Similarity", f"{min_sim:.3f}")
            
            with metric_cols[3]:
                st.metric("Max Similarity", f"{max_sim:.3f}")
        
        # Similarity Distribution
        st.subheader("Similarity Distribution")
        
        # Flatten the matrix and remove diagonal (self-similarity)
        flat_sim = []
        for i in range(len(similarity_df)):
            for j in range(i+1, len(similarity_df.columns)):
                sim = similarity_df.iloc[i, j]
                flat_sim.append(sim)
        
        fig, ax = plt.subplots(figsize=(8, 5))
        sns.histplot(flat_sim, bins=20, kde=True, ax=ax)
        ax.set_xlabel("Similarity Score")
        ax.set_ylabel("Frequency")
        ax.set_title(f"Distribution of Job Similarity Scores ({selected_dept})")
        st.pyplot(fig)
    
    with col2:
        st.header("Job Similarity Heatmap")
        
        # Display the heatmap
        if selected_dept != "All Departments":
            heatmap_file = os.path.join(run_dir, f"heatmap_{selected_dept}.png")
            if os.path.exists(heatmap_file):
                st.image(heatmap_file)
            else:
                # Generate heatmap on the fly
                st.subheader(f"Similarity Heatmap for {selected_dept}")
                fig, ax = plt.subplots(figsize=(10, 8))
                
                # If too many jobs, limit to a manageable number
                if len(similarity_df) > 30:
                    st.warning(f"Heatmap limited to first 30 jobs (out of {len(similarity_df)})")
                    heatmap_df = similarity_df.iloc[:30, :30]
                else:
                    heatmap_df = similarity_df
                
                sns.heatmap(
                    heatmap_df, 
                    cmap=color_scheme,
                    vmin=0, vmax=1,
                    annot=len(heatmap_df) < 15,  # Only show annotations if fewer than 15 jobs
                    fmt=".2f", 
                    ax=ax
                )
                ax.set_title(f"Job Similarity Heatmap - {selected_dept}")
                plt.tight_layout()
                st.pyplot(fig)
        else:
            st.info("Select a specific department to view its heatmap")
    
    # Top Similar Job Pairs
    st.header("Top Similar Job Pairs")
    
    # Extract top pairs
    job_pairs = []
    for i in range(len(similarity_df.index)):
        for j in range(i+1, len(similarity_df.columns)):  # Only upper triangle to avoid duplicates
            job1_id = similarity_df.index[i]
            job2_id = similarity_df.columns[j]
            sim_score = similarity_df.iloc[i, j]
            
            if sim_score >= similarity_threshold:
                job_pairs.append({
                    'job1_id': job1_id,
                    'job2_id': job2_id,
                    'similarity': sim_score
                })
    
    # Sort by similarity and get top N
    job_pairs.sort(key=lambda x: x['similarity'], reverse=True)
    top_job_pairs = job_pairs[:top_n_pairs]
    
    if top_job_pairs:
        # Display as a table
        top_pairs_df = pd.DataFrame(top_job_pairs)
        
        # Add job titles if we have metadata
        if jobs_metadata is not None:
            job_id_to_title = dict(zip(jobs_metadata['job_id'], jobs_metadata['title']))
            top_pairs_df['job1_title'] = top_pairs_df['job1_id'].map(job_id_to_title)
            top_pairs_df['job2_title'] = top_pairs_df['job2_id'].map(job_id_to_title)
            
            # Reorder columns to show titles first
            top_pairs_df = top_pairs_df[['job1_id', 'job1_title', 'job2_id', 'job2_title', 'similarity']]
        
        # Format the similarity scores
        top_pairs_df['similarity'] = top_pairs_df['similarity'].map(lambda x: f"{x:.3f}")
        
        st.dataframe(top_pairs_df, use_container_width=True)
    else:
        st.info(f"No job pairs found with similarity above {similarity_threshold}")
    
    # Job Search
    st.header("Job Similarity Search")
    
    # Create a way to search for a specific job
    job_options = list(similarity_df.index)
    selected_job = st.selectbox("Select Job", options=job_options)
    
    if selected_job:
        # Get similar jobs to the selected job
        similarities = similarity_df.loc[selected_job].sort_values(ascending=False)
        
        # Remove self-similarity
        similarities = similarities[similarities.index != selected_job]
        
        # Filter by threshold
        similarities = similarities[similarities >= similarity_threshold]
        
        # Limit to top N
        similarities = similarities.head(top_n_pairs)
        
        if not similarities.empty:
            # Create a dataframe for display
            similar_jobs_df = pd.DataFrame({
                'job_id': similarities.index,
                'similarity': similarities.values
            })
            
            # Add job titles if we have metadata
            if jobs_metadata is not None:
                job_id_to_title = dict(zip(jobs_metadata['job_id'], jobs_metadata['title']))
                similar_jobs_df['job_title'] = similar_jobs_df['job_id'].map(job_id_to_title)
                
                # Reorder columns to show titles first
                similar_jobs_df = similar_jobs_df[['job_id', 'job_title', 'similarity']]
            
            # Format the similarity scores
            similar_jobs_df['similarity'] = similar_jobs_df['similarity'].map(lambda x: f"{x:.3f}")
            
            st.subheader(f"Jobs Most Similar to {selected_job}")
            st.dataframe(similar_jobs_df, use_container_width=True)
            
            # Visualize the similarities
            st.subheader("Similarity Visualization")
            
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Bar chart of similarities
            bars = ax.barh(
                similar_jobs_df['job_id'].astype(str),
                similar_jobs_df['similarity'].astype(float),
                color=plt.cm.get_cmap(color_scheme)(similar_jobs_df['similarity'].astype(float))
            )
            
            ax.set_xlabel("Similarity Score")
            ax.set_title(f"Jobs Most Similar to {selected_job}")
            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.info(f"No similar jobs found with similarity above {similarity_threshold}")
    
    # Provide instructions for running new analyses
    st.header("Run New Analysis")
    st.markdown("""
    To run a new analysis, use the following command:
    ```
    python main.py --skills-file data/poc/skills_data_XXXXXXXX_XXXXXX.csv --jobs-file data/poc/jobs_data_XXXXXXXX_XXXXXX.csv
    ```
    
    Replace `XXXXXXXX_XXXXXX` with the actual timestamp in your filenames. For more options:
    ```
    python main.py --help
    ```
    """)

except Exception as e:
    st.error(f"Error: {str(e)}")
    st.exception(e)

# Show footer
st.markdown("---")
st.markdown(
    "Skill Similarity Engine POC - Created with Streamlit", 
    help="This web app provides a simple interface for exploring job similarity analysis results."
) 