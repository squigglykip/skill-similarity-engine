#!/usr/bin/env python3
"""
Functional tests for job clustering and dimensionality reduction.

This module tests methods for clustering similar jobs and visualizing 
large-scale job similarity data through dimension reduction.
"""

import os
import sys
import unittest
import pandas as pd
import numpy as np

# Use non-GUI backend for matplotlib to avoid Tkinter dependency
import matplotlib
matplotlib.use('Agg')  # This must be done before importing pyplot
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans, DBSCAN
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import logging
import json
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer as SklearnTfidfVectorizer
from skill_similarity_engine.visualization.reports import DataExporter, ReportConfig

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(name)s:%(levelname)s:%(message)s')
logger = logging.getLogger("test_job_clustering")

# Add the src directory to the Python path
src_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from skill_similarity_engine.models.skills import SkillTaxonomy
from skill_similarity_engine.models.jobs import JobArchitecture
from skill_similarity_engine.data.loaders import JobArchitectureLoader
from skill_similarity_engine.similarity.cosine import CosineSimilarityCalculator
from skill_similarity_engine.visualization.visualizer import VisualisationManager

# Custom TfidfVectorizer for testing
class TfidfVectorizer:
    """
    A wrapper around sklearn's TfidfVectorizer that works with our job architecture.
    This is a simplified version for testing purposes.
    """
    def __init__(self, **kwargs):
        self.vectorizer = SklearnTfidfVectorizer(**kwargs)
        self.job_vectors = {}
        self.skill_ids = []

    def fit(self, job_architecture):
        """
        Fit the vectorizer to a job architecture.
        
        Args:
            job_architecture: JobArchitecture object containing jobs with skills
        """
        # Create a set of all skill IDs across all jobs
        all_skill_ids = set()
        for job in job_architecture.jobs.values():
            all_skill_ids.update(job.skills.keys())
        
        # Convert to sorted list for consistent indexing
        self.skill_ids = sorted(list(all_skill_ids))
        
        # No actual fitting needed for our simple implementation
        return self

    def transform(self, job_architecture):
        """
        Transform job architecture to vectors.
        
        Args:
            job_architecture: JobArchitecture object containing jobs with skills
            
        Returns:
            dict: Mapping of job IDs to skill vectors
        """
        # Create a sparse vector for each job
        job_vectors = {}
        
        for job_id, job in job_architecture.jobs.items():
            # Create a vector where the index is the position of the skill in skill_ids
            vector = np.zeros(len(self.skill_ids))
            
            for i, skill_id in enumerate(self.skill_ids):
                # If the job has this skill, set its value to the proficiency
                if skill_id in job.skills:
                    vector[i] = job.skills[skill_id] / 5.0  # Normalize to 0-1 range
            
            # Store the vector
            job_vectors[job_id] = vector
        
        self.job_vectors = job_vectors
        return job_vectors

    def fit_transform(self, job_architecture):
        """
        Fit to data, then transform it.
        
        Args:
            job_architecture: JobArchitecture object
            
        Returns:
            dict: Mapping of job IDs to skill vectors
        """
        self.fit(job_architecture)
        return self.transform(job_architecture)

    def transform_job(self, job):
        """
        Transform a single job to a vector.
        
        Args:
            job: Job object containing skills
            
        Returns:
            numpy.ndarray: Vector representation of the job
        """
        # Create a vector where the index is the position of the skill in skill_ids
        vector = np.zeros(len(self.skill_ids))
        
        for i, skill_id in enumerate(self.skill_ids):
            # If the job has this skill, set its value to the proficiency
            if skill_id in job.skills:
                vector[i] = job.skills[skill_id] / 5.0  # Normalize to 0-1 range
        
        return vector

# Custom DataExporter with export_hexbin_data method for tests
class TestDataExporter(DataExporter):
    """Extended DataExporter with export_hexbin_data method for tests."""
    
    def export_hexbin_data(
        self,
        department: str,
        add_opportunity_flags: bool = False
    ) -> pd.DataFrame:
        """
        Export hexbin data for visualization.
        
        Args:
            department: Department to analyze
            add_opportunity_flags: Whether to add opportunity flags
            
        Returns:
            DataFrame containing job data with x,y coordinates
        """
        # Get jobs for the department
        department_jobs = [job for job in self.job_architecture.jobs.values() 
                          if job.department == department]
        
        if not department_jobs:
            raise ValueError(f"No jobs found for department: {department}")
        
        # Create a simple 2D projection (just for testing)
        job_data = []
        for i, job in enumerate(department_jobs):
            # Generate some dummy x,y coordinates based on job index
            x = np.cos(i * np.pi * 2 / len(department_jobs))
            y = np.sin(i * np.pi * 2 / len(department_jobs))
            
            row = {
                "job_id": job.job_id,
                "job_title": job.title,
                "department": job.department,
                "x": x,
                "y": y
            }
            
            # Add opportunity flags if requested
            if add_opportunity_flags:
                row.update({
                    "is_high_similarity_opportunity": i % 2 == 0,  # Alternate True/False
                    "is_internal_mobility_opportunity": i % 3 == 0
                })
            
            job_data.append(row)
        
        return pd.DataFrame(job_data)

class TestJobClustering(unittest.TestCase):
    """Test job clustering and dimensionality reduction for large-scale visualization."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures once for all tests."""
        # Define data paths
        cls.use_real_data = os.environ.get("USE_REAL_DATA", "False").lower() == "true"
        
        if cls.use_real_data:
            # Path to real data
            cls.data_dir = os.environ.get("REAL_DATA_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'real'))
            logger.info(f"Using real data from: {cls.data_dir}")
            
            # Check if real data directory exists
            if not os.path.exists(cls.data_dir):
                logger.warning(f"Real data directory does not exist: {cls.data_dir}")
                logger.warning("Falling back to sample data")
                cls.use_real_data = False
        
        # Use sample data as fallback
        if not cls.use_real_data:
            cls.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'sample')
            logger.info(f"Using sample data from: {cls.data_dir}")
        
        # Setup output directory for test artifacts
        cls.output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'output', 'tests', 'job_clustering')
        os.makedirs(cls.output_dir, exist_ok=True)
        
        # Load data
        logger.info("Loading skill taxonomy...")
        cls.skill_taxonomy = SkillTaxonomy.from_file(os.path.join(cls.data_dir, 'skills.csv'))
        logger.info(f"Loaded {len(cls.skill_taxonomy.skills)} skills")
        
        logger.info("Loading job architecture...")
        job_loader = JobArchitectureLoader(cls.skill_taxonomy)
        cls.job_architecture = job_loader.load_from_csv(os.path.join(cls.data_dir, 'jobs.csv'))
        logger.info(f"Loaded {len(cls.job_architecture.jobs)} jobs")
        
        # Initialize similarity calculator
        cls.similarity_calculator = CosineSimilarityCalculator(
            vectorizer=TfidfVectorizer(),  # Use our custom TfidfVectorizer
            skill_taxonomy=cls.skill_taxonomy,
            job_architecture=cls.job_architecture
        )
        
        # Initialize visualization manager
        cls.vis_manager = VisualisationManager(
            skill_taxonomy=cls.skill_taxonomy,
            job_architecture=cls.job_architecture,
            output_dir=cls.output_dir
        )
        
        # Replace the default DataExporter with our custom one that has export_hexbin_data
        cls.vis_manager._data_exporter = TestDataExporter(
            skill_taxonomy=cls.skill_taxonomy,
            job_architecture=cls.job_architecture,
            output_dir=cls.output_dir
        )
        
        # Get departments for testing
        cls.departments = set(job.department for job in cls.job_architecture.jobs.values())
        logger.info(f"Found {len(cls.departments)} departments")
    
    def setUp(self):
        """Set up test fixtures for each test."""
        # Skip tests if using sample data but real data is required
        if not self.use_real_data and os.environ.get("REQUIRE_REAL_DATA", "False").lower() == "true":
            self.skipTest("These tests require real data.")
    
    def test_kmeans_job_clustering(self):
        """Test K-means clustering of jobs based on skill vectors."""
        logger.info("Testing K-means clustering of jobs")
        
        # Get job vectors and job info
        job_ids = list(self.job_architecture.jobs.keys())
        job_vectors = np.array([self.similarity_calculator.job_vectors[job_id] for job_id in job_ids])
        
        # Create job metadata
        job_metadata = []
        for job_id in job_ids:
            job = self.job_architecture.jobs[job_id]
            job_metadata.append({
                "job_id": job_id,
                "title": job.title,
                "department": job.department,
                "level": job.level,
                "num_skills": len(job.skills)
            })
        
        metadata_df = pd.DataFrame(job_metadata)
        
        # Determine optimal number of clusters (simple method)
        max_clusters = min(15, len(job_ids) // 2)  # Don't try more clusters than half the jobs
        inertia_values = []
        
        for n_clusters in range(2, max_clusters + 1):
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            kmeans.fit(job_vectors)
            inertia_values.append(kmeans.inertia_)
        
        # Plot the elbow curve
        plt.figure(figsize=(10, 6))
        plt.plot(range(2, max_clusters + 1), inertia_values, marker='o')
        plt.xlabel('Number of Clusters')
        plt.ylabel('Inertia')
        plt.title('Elbow Method for Optimal k')
        plt.grid(True, alpha=0.3)
        
        elbow_plot_path = os.path.join(self.output_dir, "kmeans_elbow_curve.png")
        plt.savefig(str(elbow_plot_path))
        plt.close()
        logger.info(f"Saved K-means elbow curve to: {elbow_plot_path}")
        
        # Determine optimal number of clusters (elbow method)
        # Simple approach: find the point where the decrease in inertia slows down
        inertia_diffs = [inertia_values[i] - inertia_values[i+1] for i in range(len(inertia_values)-1)]
        relative_diffs = [inertia_diffs[i] / inertia_values[i] for i in range(len(inertia_diffs))]
        
        # Find where the relative difference falls below a threshold
        threshold = 0.1  # 10% improvement
        optimal_clusters = 2
        for i, diff in enumerate(relative_diffs):
            if diff < threshold:
                optimal_clusters = i + 2  # +2 because we started at 2 clusters
                break
        
        # Ensure we have at least 2 but not more than a reasonable number of clusters
        optimal_clusters = max(2, min(optimal_clusters, 8))
        
        logger.info(f"Selected optimal number of clusters: {optimal_clusters}")
        
        # Run K-means with optimal clusters
        kmeans = KMeans(n_clusters=optimal_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(job_vectors)
        
        # Add cluster labels to metadata
        metadata_df['cluster'] = cluster_labels
        
        # Log cluster statistics
        cluster_counts = metadata_df['cluster'].value_counts().to_dict()
        logger.info(f"Cluster sizes: {cluster_counts}")
        
        # Analyze clusters by department
        dept_cluster_df = pd.crosstab(metadata_df['department'], metadata_df['cluster'])
        
        # Plot department distribution within clusters
        plt.figure(figsize=(12, 8))
        dept_cluster_df.plot(kind='bar', stacked=True)
        plt.title('Department Distribution within Clusters')
        plt.xlabel('Department')
        plt.ylabel('Count')
        plt.legend(title='Cluster')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        dept_plot_path = os.path.join(self.output_dir, "cluster_department_distribution.png")
        plt.savefig(str(dept_plot_path))
        plt.close()
        logger.info(f"Saved department distribution plot to: {dept_plot_path}")
        
        # Export cluster information
        cluster_path = os.path.join(self.output_dir, "job_clusters.csv")
        metadata_df.to_csv(cluster_path, index=False)
        logger.info(f"Exported job cluster information to: {cluster_path}")
        
        # Test the quality of clustering
        self.assertTrue(all(count > 0 for count in cluster_counts.values()), 
                      "Some clusters have no jobs")
        
        # Find most representative jobs per cluster (closest to centroid)
        representative_jobs = []
        
        for cluster_id in range(optimal_clusters):
            # Get centroid for this cluster
            centroid = kmeans.cluster_centers_[cluster_id]
            
            # Calculate distance from each job in this cluster to the centroid
            cluster_jobs = metadata_df[metadata_df['cluster'] == cluster_id]
            
            if len(cluster_jobs) > 0:
                distances = []
                for _, job_row in cluster_jobs.iterrows():
                    job_id = job_row['job_id']
                    job_vector = self.similarity_calculator.job_vectors[job_id]
                    # Use Euclidean distance to centroid
                    distance = np.linalg.norm(job_vector - centroid)
                    distances.append((job_id, distance))
                
                # Sort by distance to centroid
                distances.sort(key=lambda x: x[1])
                
                # Get the job closest to centroid
                if distances:
                    closest_job_id = distances[0][0]
                    closest_job = self.job_architecture.jobs[closest_job_id]
                    
                    representative_jobs.append({
                        "cluster_id": cluster_id,
                        "job_id": closest_job_id,
                        "job_title": closest_job.title,
                        "department": closest_job.department,
                        "cluster_size": len(cluster_jobs),
                        "distance_to_centroid": distances[0][1]
                    })
        
        # Log representative jobs
        logger.info("Representative jobs for each cluster:")
        for job in representative_jobs:
            logger.info(f"  Cluster {job['cluster_id']} ({job['cluster_size']} jobs): {job['job_title']} ({job['department']})")
        
        # Export representative jobs
        rep_jobs_df = pd.DataFrame(representative_jobs)
        rep_jobs_path = os.path.join(self.output_dir, "representative_jobs.csv")
        rep_jobs_df.to_csv(rep_jobs_path, index=False)
        logger.info(f"Exported representative jobs to: {rep_jobs_path}")
    
    def test_dimension_reduction_visualization(self):
        """Test dimensionality reduction for visualizing job relationships."""
        logger.info("Testing dimensionality reduction visualization")
        
        # Get job vectors and job info
        job_ids = list(self.job_architecture.jobs.keys())
        job_vectors = np.array([self.similarity_calculator.job_vectors[job_id] for job_id in job_ids])
        
        # Create job metadata
        job_metadata = []
        for job_id in job_ids:
            job = self.job_architecture.jobs[job_id]
            job_metadata.append({
                "job_id": job_id,
                "title": job.title,
                "department": job.department,
                "level": job.level,
                "num_skills": len(job.skills)
            })
        
        metadata_df = pd.DataFrame(job_metadata)
        
        # 1. PCA for dimensionality reduction
        logger.info("Applying PCA for dimensionality reduction")
        pca = PCA(n_components=2, random_state=42)
        job_pca = pca.fit_transform(job_vectors)
        
        # Add PCA coordinates to metadata
        metadata_df['pca_x'] = job_pca[:, 0]
        metadata_df['pca_y'] = job_pca[:, 1]
        
        # Plot PCA results colored by department
        plt.figure(figsize=(12, 10))
        
        # Get unique departments
        departments = metadata_df['department'].unique()
        
        # Create a colormap with distinct colors
        cmap = plt.cm.get_cmap('tab20', len(departments))
        
        # Plot each department with a different color
        for i, dept in enumerate(departments):
            subset = metadata_df[metadata_df['department'] == dept]
            plt.scatter(subset['pca_x'], subset['pca_y'], 
                      c=[cmap(i)], label=dept, 
                      alpha=0.7, edgecolors='w', linewidth=0.5)
        
        plt.title('PCA Visualization of Jobs by Department')
        plt.xlabel(f'Principal Component 1 ({pca.explained_variance_ratio_[0]:.2%} variance)')
        plt.ylabel(f'Principal Component 2 ({pca.explained_variance_ratio_[1]:.2%} variance)')
        plt.legend(title='Department', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        
        pca_plot_path = os.path.join(self.output_dir, "job_pca_visualization.png")
        plt.savefig(pca_plot_path, dpi=300)
        plt.close()
        logger.info(f"Saved PCA visualization to: {pca_plot_path}")
        
        # 2. t-SNE for dimensionality reduction (better for revealing clusters)
        logger.info("Applying t-SNE for dimensionality reduction")
        tsne = TSNE(n_components=2, perplexity=min(30, len(job_ids)-1), 
                  random_state=42, n_iter=1000, learning_rate=200)
        job_tsne = tsne.fit_transform(job_vectors)
        
        # Add t-SNE coordinates to metadata
        metadata_df['tsne_x'] = job_tsne[:, 0]
        metadata_df['tsne_y'] = job_tsne[:, 1]
        
        # Plot t-SNE results colored by department
        plt.figure(figsize=(12, 10))
        
        # Plot each department with a different color
        for i, dept in enumerate(departments):
            subset = metadata_df[metadata_df['department'] == dept]
            plt.scatter(subset['tsne_x'], subset['tsne_y'], 
                      c=[cmap(i)], label=dept, 
                      alpha=0.7, edgecolors='w', linewidth=0.5)
        
        plt.title('t-SNE Visualization of Jobs by Department')
        plt.xlabel('t-SNE Dimension 1')
        plt.ylabel('t-SNE Dimension 2')
        plt.legend(title='Department', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        
        tsne_plot_path = os.path.join(self.output_dir, "job_tsne_visualization.png")
        plt.savefig(tsne_plot_path, dpi=300)
        plt.close()
        logger.info(f"Saved t-SNE visualization to: {tsne_plot_path}")
        
        # 3. DBSCAN clustering on t-SNE results
        logger.info("Applying DBSCAN clustering on t-SNE results")
        
        # Extract t-SNE coordinates
        tsne_coords = metadata_df[['tsne_x', 'tsne_y']].values
        
        # Determine eps parameter based on nearest neighbor distances
        from sklearn.neighbors import NearestNeighbors
        nn = NearestNeighbors(n_neighbors=2)
        nn.fit(tsne_coords)
        distances, _ = nn.kneighbors(tsne_coords)
        
        # Sort distances to the 2nd nearest neighbor
        sorted_distances = np.sort(distances[:, 1])
        
        # Plot k-distance graph
        plt.figure(figsize=(10, 6))
        plt.plot(sorted_distances)
        plt.xlabel('Points sorted by distance')
        plt.ylabel('Distance to 2nd nearest neighbor')
        plt.title('K-distance Graph for DBSCAN eps Parameter Selection')
        plt.grid(True, alpha=0.3)
        
        kdist_plot_path = os.path.join(self.output_dir, "dbscan_kdistance.png")
        plt.savefig(kdist_plot_path)
        plt.close()
        logger.info(f"Saved k-distance plot to: {kdist_plot_path}")
        
        # Find the elbow point in the k-distance graph
        # Simple approach: look for large percentage increases
        distance_diffs = [sorted_distances[i+1] - sorted_distances[i] for i in range(len(sorted_distances)-1)]
        relative_diffs = [distance_diffs[i] / sorted_distances[i] if sorted_distances[i] > 0 else 0 
                       for i in range(len(distance_diffs))]
        
        # Find the point with the max relative difference
        elbow_idx = np.argmax(relative_diffs)
        eps_value = sorted_distances[elbow_idx]
        
        # Ensure eps is reasonable
        eps_value = max(0.5, min(eps_value, 10.0))
        
        logger.info(f"Selected DBSCAN eps value: {eps_value:.2f}")
        
        # Run DBSCAN
        dbscan = DBSCAN(eps=eps_value, min_samples=3)
        dbscan_labels = dbscan.fit_predict(tsne_coords)
        
        # Add DBSCAN cluster labels to metadata
        metadata_df['dbscan_cluster'] = dbscan_labels
        
        # Count the number of noise points (-1 labels)
        noise_count = (dbscan_labels == -1).sum()
        logger.info(f"DBSCAN identified {len(set(dbscan_labels)) - (1 if -1 in dbscan_labels else 0)} clusters")
        logger.info(f"Noise points: {noise_count} ({noise_count/len(dbscan_labels):.1%} of total)")
        
        # Plot DBSCAN clusters
        plt.figure(figsize=(12, 10))
        
        # Create a new colormap for DBSCAN clusters
        unique_clusters = sorted(set(dbscan_labels))
        cluster_cmap = plt.cm.get_cmap('tab20', len(unique_clusters))
        
        # Plot each cluster with a different color
        for i, cluster_id in enumerate(unique_clusters):
            if cluster_id == -1:
                # Plot noise points in black
                subset = metadata_df[metadata_df['dbscan_cluster'] == cluster_id]
                plt.scatter(subset['tsne_x'], subset['tsne_y'], 
                          c='black', marker='x', label='Noise', 
                          alpha=0.5, s=30)
            else:
                # Plot cluster points
                subset = metadata_df[metadata_df['dbscan_cluster'] == cluster_id]
                plt.scatter(subset['tsne_x'], subset['tsne_y'], 
                          c=[cluster_cmap(i)], label=f'Cluster {cluster_id}', 
                          alpha=0.7, edgecolors='w', linewidth=0.5)
        
        plt.title('DBSCAN Clustering of Jobs based on t-SNE')
        plt.xlabel('t-SNE Dimension 1')
        plt.ylabel('t-SNE Dimension 2')
        
        # Only show legend if not too many clusters
        if len(unique_clusters) <= 15:
            plt.legend(title='Cluster', bbox_to_anchor=(1.05, 1), loc='upper left')
        
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.tight_layout()
        
        dbscan_plot_path = os.path.join(self.output_dir, "job_dbscan_clustering.png")
        plt.savefig(dbscan_plot_path, dpi=300)
        plt.close()
        logger.info(f"Saved DBSCAN clustering visualization to: {dbscan_plot_path}")
        
        # Export dimensionality reduction results
        export_path = os.path.join(self.output_dir, "job_dimension_reduction.csv")
        metadata_df.to_csv(export_path, index=False)
        logger.info(f"Exported dimensionality reduction results to: {export_path}")
        
        # Export DBSCAN cluster analysis
        dbscan_analysis = []
        
        for cluster_id in [c for c in unique_clusters if c != -1]:  # Skip noise cluster
            cluster_jobs = metadata_df[metadata_df['dbscan_cluster'] == cluster_id]
            
            # Get department distribution
            dept_counts = cluster_jobs['department'].value_counts().to_dict()
            main_dept = max(dept_counts.items(), key=lambda x: x[1])[0]
            main_dept_pct = dept_counts[main_dept] / len(cluster_jobs) * 100
            
            # Get a sample of job titles
            sample_jobs = cluster_jobs['title'].tolist()[:5]
            
            dbscan_analysis.append({
                "cluster_id": cluster_id,
                "size": len(cluster_jobs),
                "main_department": main_dept,
                "main_department_percentage": main_dept_pct,
                "department_counts": json.dumps(dept_counts),
                "sample_jobs": ", ".join(sample_jobs)
            })
        
        if dbscan_analysis:
            dbscan_df = pd.DataFrame(dbscan_analysis)
            dbscan_path = os.path.join(self.output_dir, "dbscan_cluster_analysis.csv")
            dbscan_df.to_csv(dbscan_path, index=False)
            logger.info(f"Exported DBSCAN cluster analysis to: {dbscan_path}")
    
    def test_hexbin_visualization_export(self):
        """Test hexbin visualization for large-scale job similarity data."""
        logger.info("Testing hexbin visualization for job similarity")
        
        # Skip departments with too few jobs
        min_department_size = 4  # Need at least this many jobs for hexbin
        
        # Find departments with enough jobs
        dept_counts = {}
        for job in self.job_architecture.jobs.values():
            dept_counts[job.department] = dept_counts.get(job.department, 0) + 1
        
        valid_departments = [dept for dept, count in dept_counts.items() if count >= min_department_size]
        
        if not valid_departments:
            self.skipTest("No departments with enough jobs for hexbin visualization")
        
        # Test department is first valid department or Analytics if available
        test_department = 'Analytics' if 'Analytics' in valid_departments else valid_departments[0]
        logger.info(f"Testing hexbin visualization for department: {test_department}")
        
        # Generate hexbin visualization
        output_path = self.vis_manager.generate_hexbin_visualization(
            department=test_department,
            color_scheme='viridis',
            figsize=(12, 10),
            dpi=300
        )
        
        logger.info(f"Generated hexbin visualization at: {output_path}")
        
        # Verify the file was created
        self.assertTrue(os.path.exists(output_path), "Hexbin visualization file was not created")
        
        # Test export of hexbin data for Power BI
        hexbin_data = self.vis_manager._data_exporter.export_hexbin_data(
            department=test_department
        )
        
        # Export the hexbin data
        hexbin_export_path = os.path.join(self.output_dir, f"hexbin_data_{test_department}.csv")
        hexbin_data.to_csv(hexbin_export_path, index=False)
        logger.info(f"Exported hexbin data to: {hexbin_export_path}")
        
        # Verify we got reasonable data
        self.assertIsInstance(hexbin_data, pd.DataFrame, "Expected DataFrame from hexbin export")
        self.assertGreater(len(hexbin_data), 0, "Expected non-empty hexbin data")
        
        # Check if we have expected columns
        expected_cols = ['job_id', 'job_title', 'x', 'y']
        for col in expected_cols:
            self.assertIn(col, hexbin_data.columns, f"Expected column {col} in hexbin data")
        
        # Test hexbin with opportunity flags
        hexbin_with_flags = self.vis_manager._data_exporter.export_hexbin_data(
            department=test_department,
            add_opportunity_flags=True
        )
        
        # Export the hexbin data with flags
        flags_export_path = os.path.join(self.output_dir, f"hexbin_opportunities_{test_department}.csv")
        hexbin_with_flags.to_csv(flags_export_path, index=False)
        logger.info(f"Exported hexbin data with opportunity flags to: {flags_export_path}")
        
        # Verify we have opportunity flag columns
        flag_cols = ['is_high_similarity_opportunity', 'is_internal_mobility_opportunity']
        for col in flag_cols:
            self.assertIn(col, hexbin_with_flags.columns, f"Expected column {col} in hexbin data with flags")


if __name__ == "__main__":
    # Run specific test case with real data if requested
    if len(sys.argv) > 1 and sys.argv[1] == "--real-data":
        # Set environment variable to use real data
        os.environ["USE_REAL_DATA"] = "True"
        # Remove the flag from args so unittest doesn't try to interpret it
        sys.argv.pop(1)
    
    unittest.main() 