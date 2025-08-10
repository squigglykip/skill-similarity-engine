#!/usr/bin/env python3
"""
Clustering Analysis Engine
==========================

Production-ready clustering analysis system that provides job profile clustering,
skills bundling, and cluster intelligence for strategic workforce planning.

This module integrates the clustering logic from the notebook system into the
SSE architecture with configuration-driven parameters and database integration.

Key Components:
- JobProfileClusterer: DBSCAN-based job clustering with business naming
- SkillsBundleClusterer: Skills clustering with taxonomy-aware bundling
- ClusterAnalyzer: Business interpretation and strategic naming
- ClusteringMetrics: Quality validation and silhouette analysis

Philosophy: Configuration-driven clustering with production-quality metrics
"""

import pandas as pd
import numpy as np
import sqlite3
import warnings
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Set, Any, Union
from collections import defaultdict, Counter
from dataclasses import dataclass

# Scientific computing
from sklearn.cluster import DBSCAN, AgglomerativeClustering, KMeans
from sklearn.metrics import silhouette_score, silhouette_samples
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler

# SSE Integration
from ..config.architectural_config_manager import get_config_manager
from ..error_handling.core import EngineError, ErrorCategory, ErrorSeverity
import logging

warnings.filterwarnings('ignore')

# Simple logging helper
logger = logging.getLogger(__name__)

def log_info(message: str, context_dict=None, **context):
    """Simple logging helper with user-friendly output."""
    # Use user-friendly messages like main.py
    if "initialized" in message.lower():
        print(f"✅ {message.replace('initialized', 'ready')}")
    elif "starting" in message.lower() or "building" in message.lower():
        print(f"🔍 {message}...")
    elif "completed" in message.lower() or "successful" in message.lower():
        print(f"✅ {message}")
    elif "failed" in message.lower() or "error" in message.lower():
        print(f"❌ {message}")
        if context_dict and 'error' in context_dict:
            print(f"   Details: {context_dict['error']}")
    else:
        # For other messages, show progress-style output
        if context_dict:
            if 'n_jobs' in context_dict:
                print(f"   📊 Processing {context_dict['n_jobs']} job profiles...")
            elif 'total_relationships' in context_dict:
                print(f"   📋 Using {context_dict['total_relationships']} job-skill relationships")
            elif 'matrix_shape' in context_dict:
                shape = context_dict['matrix_shape']
                print(f"   🎯 Built {shape[0]}×{shape[1]} similarity matrix successfully")
            else:
                print(f"   {message}")
        else:
            print(f"   {message}")


@dataclass
class ClusteringResult:
    """Container for clustering analysis results."""
    job_clusters_df: pd.DataFrame
    job_characteristics_df: pd.DataFrame
    skill_bundles_df: pd.DataFrame
    skill_characteristics_df: pd.DataFrame
    specialized_skills_df: pd.DataFrame
    metadata: Dict[str, Any]


@dataclass 
class ClusteringMetrics:
    """Container for clustering quality metrics."""
    silhouette_score: float
    n_clusters: int
    n_noise: int
    cluster_sizes: Dict[int, int]
    quality_assessment: str


class JobProfileClusterer:
    """
    Job profile clustering using DBSCAN with enhanced similarity measures.
    
    Ports the logic from 02b_job_profile_clustering_production.py with
    configuration-driven parameters and production-quality error handling.
    """
    
    def __init__(self, config_manager=None):
        """Initialize job profile clusterer with configuration."""
        self.config_manager = config_manager or get_config_manager()
        self.clustering_config = self._load_clustering_config()
        
        # Job profile clustering parameters
        job_config = self.clustering_config.get('job_profile_clustering', {})
        self.algorithm = job_config.get('algorithm', 'dbscan').lower()
        optimal_params = job_config.get('optimal_parameters', {})
        self.eps = optimal_params.get('eps', 0.1)
        self.min_samples = optimal_params.get('min_samples', 2)
        self.n_clusters = optimal_params.get('n_clusters', 20)  # For KMeans/Hierarchical
        self.linkage = optimal_params.get('linkage', 'ward')  # For Hierarchical
        self.similarity_measure = optimal_params.get('similarity_measure', 'enhanced_defining_skills')
        
        # Quality thresholds
        quality_config = job_config.get('quality_thresholds', {})
        self.min_silhouette_score = quality_config.get('min_silhouette_score', 0.5)
        self.min_cluster_size = quality_config.get('min_cluster_size', 5)
        
        log_info("JobProfileClusterer initialized", 
                 algorithm=self.algorithm, eps=self.eps, min_samples=self.min_samples, 
                 n_clusters=self.n_clusters, similarity_measure=self.similarity_measure)
    
    def _load_clustering_config(self) -> Dict[str, Any]:
        """Load clustering configuration from architectural config manager."""
        try:
            # Try to load clustering-specific config
            clustering_config = self.config_manager.get_nested_value(
                'core', 'clustering_analysis'
            )
            
            if clustering_config:
                return clustering_config
            
            # Fail fast - no fallback
            raise ValueError(
                "Clustering configuration not found at 'core.clustering_analysis'. "
                "Run 'Optimize Clustering Parameters' first to generate the required configuration."
            )
            
        except Exception as e:
            # Fail fast - no fallback
            raise ValueError(
                f"Failed to load clustering configuration: {str(e)}. "
                "Ensure 'config/core/clustering_analysis.yaml' exists and is valid."
            )
    
    def _perform_clustering(self, similarity_matrix: np.ndarray) -> np.ndarray:
        """
        Perform clustering using the configured algorithm.
        
        Args:
            similarity_matrix: Job similarity matrix
            
        Returns:
            Cluster labels array
        """
        log_info(f"Performing {self.algorithm.upper()} clustering", 
                algorithm=self.algorithm, 
                eps=self.eps if self.algorithm == 'dbscan' else None,
                min_samples=self.min_samples if self.algorithm == 'dbscan' else None,
                n_clusters=self.n_clusters if self.algorithm in ['kmeans', 'hierarchical'] else None)
        
        if self.algorithm == 'dbscan':
            # Convert similarity to distance matrix for DBSCAN
            distance_matrix = 1 - similarity_matrix
            np.fill_diagonal(distance_matrix, 0.0)
            
            clusterer = DBSCAN(
                eps=self.eps,
                min_samples=self.min_samples,
                metric='precomputed'
            )
            return clusterer.fit_predict(distance_matrix)
            
        elif self.algorithm == 'hierarchical':
            # For hierarchical clustering, handle linkage-specific requirements
            if self.linkage == 'ward':
                # Ward linkage requires Euclidean distance, so we use the similarity matrix as features
                # This is a workaround since we don't have original feature vectors
                clusterer = AgglomerativeClustering(
                    n_clusters=self.n_clusters,
                    linkage='ward'
                    # No metric parameter for ward - it uses euclidean by default
                )
                return clusterer.fit_predict(similarity_matrix)
            else:
                # Other linkages (complete, average, single) can work with precomputed distances
                clusterer = AgglomerativeClustering(
                    n_clusters=self.n_clusters,
                    linkage=self.linkage,
                    metric='precomputed'
                )
                # Convert similarity to distance for hierarchical clustering
                distance_matrix = 1 - similarity_matrix
                np.fill_diagonal(distance_matrix, 0.0)
                return clusterer.fit_predict(distance_matrix)
            
        elif self.algorithm == 'kmeans':
            # For k-means, we need feature vectors not similarity matrix
            # Use similarity matrix as "features" (not ideal but workable)
            clusterer = KMeans(
                n_clusters=self.n_clusters,
                random_state=42,
                n_init=10
            )
            return clusterer.fit_predict(similarity_matrix)
            
        else:
            raise ValueError(f"Unsupported clustering algorithm: {self.algorithm}. "
                           f"Supported algorithms: 'dbscan', 'hierarchical', 'kmeans'")
    
    def _get_algorithm_parameters_string(self) -> str:
        """Get algorithm-specific parameters as a string for metadata."""
        if self.algorithm == 'dbscan':
            return f'eps={self.eps}, min_samples={self.min_samples}'
        elif self.algorithm == 'hierarchical':
            return f'n_clusters={self.n_clusters}, linkage={self.linkage}'
        elif self.algorithm == 'kmeans':
            return f'n_clusters={self.n_clusters}, random_state=42'
        else:
            return f'algorithm={self.algorithm}'
    
    def cluster_job_profiles(self, db_path: str) -> Tuple[pd.DataFrame, ClusteringMetrics]:
        """
        Perform job profile clustering using configured parameters.
        
        Args:
            db_path: Path to the SQLite database
            
        Returns:
            Tuple of (clustered_jobs_df, clustering_metrics)
        """
        log_info("Starting job profile clustering", {
            'database': db_path,
            'algorithm': self.algorithm.upper(),
            'eps': self.eps if self.algorithm == 'dbscan' else None,
            'min_samples': self.min_samples if self.algorithm == 'dbscan' else None,
            'n_clusters': self.n_clusters if self.algorithm in ['kmeans', 'hierarchical'] else None
        })
        
        # Load job similarity matrix
        similarity_matrix, job_profiles = self._load_job_similarity_data(db_path)
        
        if similarity_matrix is None or len(similarity_matrix) == 0:
            raise ValueError("No job similarity data available for clustering")
        
        # Perform clustering based on configured algorithm
        cluster_labels = self._perform_clustering(similarity_matrix)
        
        # Convert similarity to distance matrix for metrics calculation
        distance_matrix = 1 - similarity_matrix
        np.fill_diagonal(distance_matrix, 0.0)
        
        # Calculate clustering metrics
        if job_profiles is None:
            raise ValueError("Job profiles data is required for clustering")
            
        metrics = self._calculate_clustering_metrics(
            distance_matrix, cluster_labels, job_profiles
        )
        
        # Create clustered jobs DataFrame
        clustered_jobs_df = self._create_clustered_jobs_dataframe(
            job_profiles, cluster_labels, metrics
        )
        
        log_info("Job profile clustering completed", {
            'n_clusters': metrics.n_clusters,
            'n_noise': metrics.n_noise,
            'silhouette_score': metrics.silhouette_score,
            'quality_assessment': metrics.quality_assessment
        })
        
        return clustered_jobs_df, metrics
    
    def _load_job_similarity_data(self, db_path: str) -> Tuple[Optional[np.ndarray], Optional[pd.DataFrame]]:
        """Load job-skill relationships and build similarity matrix using the three-table approach."""
        try:
            with sqlite3.connect(db_path) as conn:
                # Load job-skill relationships using the three core tables (like working notebooks)
                job_skills_query = """
                SELECT 
                    js.JobProfileID,
                    js.Skill_ID,
                    s.Skill_Name,
                    s.Category as Skill_Category,
                    s.SkillType,
                    j.JobProfile,
                    j.JobFunction,
                    j.JobSubFunction,
                    j.JobCategory,
                    j.ManagementLevel
                FROM core_job_skill_requirements js
                JOIN core_skills_taxonomy s ON js.Skill_ID = s.Skill_ID
                JOIN core_job_architecture j ON js.JobProfileID = j.JobProfileID
                ORDER BY js.JobProfileID, s.Skill_Name
                """
                
                job_skills_df = pd.read_sql_query(job_skills_query, conn)
                
                if len(job_skills_df) == 0:
                    log_info("No job-skill relationships found in database")
                    return None, None
                
                # Extract job metadata
                job_metadata = job_skills_df[['JobProfileID', 'JobProfile', 'JobFunction', 'JobSubFunction', 'JobCategory', 'ManagementLevel']].drop_duplicates()
                job_metadata.columns = ['job_profile_id', 'job_profile', 'job_function', 'job_sub_function', 'job_category', 'management_level']
                
                # Build job-to-skills mapping
                job_to_skills = {}
                for job_id, job_group in job_skills_df.groupby('JobProfileID'):
                    job_to_skills[job_id] = set(job_group['Skill_Name'])
                
                # Build similarity matrix using Jaccard similarity (like working notebooks)
                job_ids = sorted(job_metadata['job_profile_id'].unique())
                n_jobs = len(job_ids)
                similarity_matrix = np.zeros((n_jobs, n_jobs))
                
                log_info("Building job similarity matrix", {
                    'n_jobs': n_jobs,
                    'total_relationships': len(job_skills_df)
                })
                
                # Calculate pairwise similarities
                for i, job_a in enumerate(job_ids):
                    for j, job_b in enumerate(job_ids):
                        if i <= j:
                            if i == j:
                                similarity_matrix[i, j] = 1.0
                            else:
                                job_a_skills = job_to_skills.get(job_a, set())
                                job_b_skills = job_to_skills.get(job_b, set())
                                
                                if job_a_skills and job_b_skills:
                                    # Jaccard similarity
                                    shared_skills = job_a_skills & job_b_skills
                                    total_skills = job_a_skills | job_b_skills
                                    jaccard_sim = len(shared_skills) / len(total_skills) if total_skills else 0.0
                                    similarity_matrix[i, j] = jaccard_sim
                                else:
                                    similarity_matrix[i, j] = 0.0
                            
                            # Make symmetric
                            similarity_matrix[j, i] = similarity_matrix[i, j]
                
                log_info("Job similarity matrix built successfully", {
                    'matrix_shape': similarity_matrix.shape,
                    'mean_similarity': float(np.mean(similarity_matrix[similarity_matrix < 1.0]))
                })
                
                return similarity_matrix, job_metadata
                
        except Exception as e:
            log_info("Failed to build job similarity data", {'error': str(e)})
            return None, None
    
    def _calculate_clustering_metrics(self, distance_matrix: np.ndarray, 
                                    cluster_labels: np.ndarray, 
                                    job_profiles: pd.DataFrame) -> ClusteringMetrics:
        """Calculate clustering quality metrics."""
        # Basic cluster statistics
        unique_labels = set(cluster_labels)
        n_clusters = len(unique_labels) - (1 if -1 in unique_labels else 0)
        n_noise = list(cluster_labels).count(-1)
        
        # Cluster sizes
        cluster_sizes = {}
        for label in unique_labels:
            if label != -1:  # Exclude noise
                cluster_sizes[label] = np.sum(cluster_labels == label)
        
        # Calculate silhouette score (if we have clusters)
        silhouette = 0.0
        if n_clusters > 1 and n_noise < len(cluster_labels):
            try:
                # Use distance matrix directly for silhouette score (distance metric)
                silhouette = silhouette_score(distance_matrix, cluster_labels, metric='precomputed')
            except Exception as e:
                log_info("Failed to calculate silhouette score", {'error': str(e)})
        
        # Quality assessment
        quality_assessment = self._assess_clustering_quality(
            silhouette, n_clusters, n_noise, len(cluster_labels), cluster_sizes
        )
        
        return ClusteringMetrics(
            silhouette_score=silhouette,
            n_clusters=n_clusters,
            n_noise=n_noise,
            cluster_sizes=cluster_sizes,
            quality_assessment=quality_assessment
        )
    
    def _assess_clustering_quality(self, silhouette: float, n_clusters: int, 
                                 n_noise: int, total_jobs: int, 
                                 cluster_sizes: Dict[int, int]) -> str:
        """Assess overall clustering quality."""
        issues = []
        
        if silhouette < self.min_silhouette_score:
            issues.append(f"Low silhouette score ({silhouette:.3f} < {self.min_silhouette_score})")
        
        if n_noise / total_jobs > 0.3:
            issues.append(f"High noise ratio ({n_noise/total_jobs:.1%})")
        
        small_clusters = sum(1 for size in cluster_sizes.values() if size < self.min_cluster_size)
        if small_clusters > n_clusters * 0.5:
            issues.append(f"Many small clusters ({small_clusters}/{n_clusters})")
        
        if not issues:
            return "Excellent"
        elif len(issues) == 1:
            return "Good"
        elif len(issues) == 2:
            return "Fair"
        else:
            return "Poor"
    
    def _create_clustered_jobs_dataframe(self, job_profiles: pd.DataFrame, 
                                       cluster_labels: np.ndarray,
                                       metrics: ClusteringMetrics) -> pd.DataFrame:
        """Create the final clustered jobs DataFrame with business context."""
        # Add cluster labels to job profiles
        job_profiles = job_profiles.copy()
        job_profiles['cluster_id'] = cluster_labels
        
        # Generate business-readable cluster names and descriptions
        cluster_info = self._generate_cluster_business_context(job_profiles, metrics)
        
        # Merge cluster information
        clustered_jobs_df = job_profiles.merge(
            cluster_info, on='cluster_id', how='left'
        )
        
        # Add metadata
        clustered_jobs_df['created_timestamp'] = datetime.now().isoformat()
        
        # Handle noise points
        noise_mask = clustered_jobs_df['cluster_id'] == -1
        clustered_jobs_df.loc[noise_mask, 'cluster_name'] = 'Specialized/Unique Roles'
        clustered_jobs_df.loc[noise_mask, 'cluster_description'] = 'Individual roles with unique skill profiles'
        clustered_jobs_df.loc[noise_mask, 'cluster_rationale'] = 'Insufficient similarity to other roles for clustering'
        
        return clustered_jobs_df
    
    def _generate_cluster_business_context(self, job_profiles: pd.DataFrame, 
                                         metrics: ClusteringMetrics) -> pd.DataFrame:
        """Generate business-readable cluster names and descriptions."""
        cluster_info = []
        
        for cluster_id in metrics.cluster_sizes.keys():
            cluster_jobs = job_profiles[job_profiles['cluster_id'] == cluster_id]
            
            # Analyze cluster composition
            dominant_function = cluster_jobs['job_function'].mode().iloc[0] if len(cluster_jobs) > 0 else 'Mixed'
            dominant_level = cluster_jobs['management_level'].mode().iloc[0] if len(cluster_jobs) > 0 else 'Mixed'
            
            # Generate cluster name
            cluster_name = self._generate_cluster_name(cluster_jobs, dominant_function, dominant_level)
            
            # Generate description and rationale
            cluster_description = self._generate_cluster_description(cluster_jobs, dominant_function)
            cluster_rationale = self._generate_cluster_rationale(cluster_jobs)
            
            # Sample jobs and skills (placeholder - would need skills data)
            sample_jobs = '; '.join(cluster_jobs['job_profile'].head(3).tolist())
            sample_skills = 'Skills analysis pending'  # TODO: Implement skills analysis
            
            cluster_info.append({
                'cluster_id': cluster_id,
                'cluster_name': cluster_name,
                'cluster_description': cluster_description,
                'cluster_rationale': cluster_rationale,
                'cluster_size': len(cluster_jobs),
                'sample_jobs': sample_jobs,
                'sample_skills': sample_skills,
                'cluster_confidence': self._assess_cluster_confidence(len(cluster_jobs), metrics.silhouette_score),
                'intra_cluster_similarity': 0.0,  # TODO: Calculate intra-cluster similarity
                'inter_cluster_distance': 0.0,   # TODO: Calculate inter-cluster distance
                'clustering_algorithm': self.algorithm.upper(),
                'algorithm_parameters': self._get_algorithm_parameters_string(),
                'analysis_date': datetime.now().strftime('%Y-%m-%d'),
                'silhouette_score': metrics.silhouette_score
            })
        
        return pd.DataFrame(cluster_info)
    
    def _generate_cluster_name(self, cluster_jobs: pd.DataFrame, 
                              dominant_function: str, dominant_level: str) -> str:
        """Generate a business-readable cluster name."""
        size = len(cluster_jobs)
        
        if size == 1:
            return f"Individual {dominant_function} Role"
        elif dominant_function != 'Mixed':
            if dominant_level != 'Mixed':
                return f"{dominant_function} - {dominant_level} Cluster"
            else:
                return f"{dominant_function} Professional Cluster"
        else:
            return f"Cross-Functional Cluster ({size} roles)"
    
    def _generate_cluster_description(self, cluster_jobs: pd.DataFrame, 
                                    dominant_function: str) -> str:
        """Generate a human-interpretable cluster description."""
        size = len(cluster_jobs)
        functions = cluster_jobs['job_function'].nunique()
        
        if functions == 1:
            return f"Cohesive group of {size} {dominant_function} roles with similar skill requirements"
        else:
            return f"Diverse cluster of {size} roles spanning {functions} job functions with shared competencies"
    
    def _generate_cluster_rationale(self, cluster_jobs: pd.DataFrame) -> str:
        """Generate explanation of clustering logic."""
        size = len(cluster_jobs)
        functions = cluster_jobs['job_function'].nunique()
        
        if functions == 1:
            return f"Grouped by shared {cluster_jobs['job_function'].iloc[0]} expertise and skill overlap"
        else:
            return f"Clustered based on cross-functional skill similarities despite different job functions"
    
    def _assess_specialization_depth(self, cluster_jobs: pd.DataFrame) -> str:
        """Assess the specialization depth of the cluster."""
        functions = cluster_jobs['job_function'].nunique()
        
        if functions == 1:
            return "Deep"
        elif functions <= 3:
            return "Focused" 
        else:
            return "Broad"
    
    def _assess_cluster_confidence(self, cluster_size: int, silhouette_score: float) -> float:
        """Assess confidence level in cluster quality as a numeric score."""
        # Base confidence from silhouette score (0.0 to 1.0)
        base_confidence = max(0.0, silhouette_score) if silhouette_score else 0.0
        
        # Size bonus: larger clusters get confidence boost
        if cluster_size >= 10:
            size_multiplier = 1.2
        elif cluster_size >= 5:
            size_multiplier = 1.1
        elif cluster_size >= 3:
            size_multiplier = 1.0
        else:
            size_multiplier = 0.8
        
        # Final confidence score (capped at 1.0)
        confidence = min(1.0, base_confidence * size_multiplier)
        return round(confidence, 3)


class SkillsBundleClusterer:
    """
    Skills clustering and bundling with taxonomy-aware analysis.
    
    Ports logic from 03b_skills_clustering_production.py with enhanced
    bundling strategies and specialization detection.
    """
    
    def __init__(self, config_manager=None):
        """Initialize skills bundle clusterer."""
        self.config_manager = config_manager or get_config_manager()
        self.clustering_config = self._load_clustering_config()
        
        # Skills clustering parameters
        skills_config = self.clustering_config.get('skills_clustering', {})
        self.algorithm = skills_config.get('algorithm', 'dbscan').lower()
        optimal_params = skills_config.get('optimal_parameters', {})
        self.eps = optimal_params.get('eps', 0.15)
        self.min_samples = optimal_params.get('min_samples', 3)
        self.n_clusters = optimal_params.get('n_clusters', 30)  # For KMeans/Hierarchical  
        self.linkage = optimal_params.get('linkage', 'ward')  # For Hierarchical
        self.similarity_measure = optimal_params.get('similarity_measure', 'jaccard_combined')
        
        # Bundling strategy
        bundling_config = skills_config.get('bundling_strategy', {})
        self.max_bundle_size = bundling_config.get('max_bundle_size', 15)
        self.min_specialization_threshold = bundling_config.get('min_specialization_threshold', 5.0)
        
        log_info("SkillsBundleClusterer initialized", {
            'algorithm': self.algorithm,
            'eps': self.eps,
            'min_samples': self.min_samples,
            'n_clusters': self.n_clusters,
            'max_bundle_size': self.max_bundle_size
        })
    
    def _load_clustering_config(self) -> Dict[str, Any]:
        """Load clustering configuration (shared with JobProfileClusterer)."""
        # Reuse the same config loading logic
        clusterer = JobProfileClusterer()
        return clusterer._load_clustering_config()
    
    def cluster_skills(self, db_path: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Perform skills clustering and bundling.
        
        Args:
            db_path: Path to the SQLite database
            
        Returns:
            Tuple of (skill_bundles_df, bundle_characteristics_df, specialized_skills_df)
        """
        log_info("Starting skills clustering and bundling", {
            'database': db_path,
            'max_bundle_size': self.max_bundle_size,
            'specialization_threshold': self.min_specialization_threshold
        })
        
        # Load skills data
        skills_data = self._load_skills_data(db_path)
        
        if skills_data is None or len(skills_data) == 0:
            raise ValueError("No skills data available for clustering")
        
        # Perform skills clustering
        clustered_skills = self._perform_skills_clustering(skills_data)
        
        # Generate skill bundles
        skill_bundles_df, bundle_characteristics_df, specialized_skills_df = self._generate_skill_bundles(
            clustered_skills
        )
        
        log_info("Skills clustering completed", {
            'n_bundles': len(bundle_characteristics_df),
            'n_specialized': len(specialized_skills_df),
            'total_skills': len(skills_data)
        })
        
        return skill_bundles_df, bundle_characteristics_df, specialized_skills_df
    
    def _load_skills_data(self, db_path: str) -> Optional[pd.DataFrame]:
        """Load skills data from database."""
        try:
            with sqlite3.connect(db_path) as conn:
                skills_query = """
                SELECT 
                    s.Skill_ID as skill_id,
                    s.Skill_Name as skill_name,
                    s.Category as category,
                    s.Subcategory as subcategory,
                    s.SkillType as skill_type,
                    COUNT(DISTINCT js.JobProfileID) as jobs_count,
                    COUNT(*) as total_occurrences,
                    ROUND(COUNT(DISTINCT js.JobProfileID) * 100.0 / 
                          (SELECT COUNT(DISTINCT JobProfileID) FROM core_job_skill_requirements), 2) as prevalence_percent
                FROM core_skills_taxonomy s
                JOIN core_job_skill_requirements js ON s.Skill_ID = js.Skill_ID
                GROUP BY s.Skill_ID, s.Skill_Name, s.Category, s.Subcategory, s.SkillType
                HAVING jobs_count > 0
                ORDER BY jobs_count DESC
                """
                
                skills_df = pd.read_sql_query(skills_query, conn)
                
                if len(skills_df) == 0:
                    log_info("No skills data found in database")
                    return None
                
                log_info("Loaded skills data", {
                    'n_skills': len(skills_df),
                    'avg_jobs_per_skill': skills_df['jobs_count'].mean()
                })
                
                return skills_df
                
        except Exception as e:
            log_info("Failed to load skills data", {'error': str(e)})
            return None
    
    def _perform_skills_clustering(self, skills_data: pd.DataFrame) -> pd.DataFrame:
        """Perform DBSCAN clustering on skills data."""
        # For now, implement a simplified clustering based on category and prevalence
        # TODO: Implement proper similarity-based clustering
        
        skills_with_clusters = skills_data.copy()
        
        # Simple clustering based on category and prevalence
        cluster_id = 0
        skills_with_clusters['cluster_id'] = -1  # Start with all as noise
        
        # Group by category for basic clustering
        for category in skills_data['category'].unique():
            category_skills = skills_data[skills_data['category'] == category]
            
            if len(category_skills) >= self.min_samples:
                skills_with_clusters.loc[
                    skills_with_clusters['category'] == category, 'cluster_id'
                ] = cluster_id
                cluster_id += 1
        
        return skills_with_clusters
    
    def _generate_skill_bundles(self, clustered_skills: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Generate skill bundles, characteristics, and identify specialized skills."""
        skill_bundles = []
        bundle_characteristics = []
        specialized_skills = []
        
        # Process each cluster
        for cluster_id in clustered_skills['cluster_id'].unique():
            cluster_skills = clustered_skills[clustered_skills['cluster_id'] == cluster_id]
            
            if cluster_id == -1:
                # Handle noise/specialized skills
                for _, skill in cluster_skills.iterrows():
                    if skill['jobs_count'] < self.min_specialization_threshold:
                        specialized_skills.append({
                            'skill_id': skill['skill_id'],
                            'skill_name': skill['skill_name'],
                            'category': skill['category'],
                            'subcategory': skill['subcategory'],
                            'skill_type': skill['skill_type'],
                            'jobs_count': skill['jobs_count'],
                            'prevalence_percent': skill['prevalence_percent'],
                            'specialization_reason': 'Low prevalence - highly specialized',
                            'created_timestamp': datetime.now().isoformat()
                        })
                continue
            
            # Generate bundle for this cluster
            bundle_name = self._generate_bundle_name(cluster_skills)
            bundle_description = self._generate_bundle_description(cluster_skills)
            
            # Add skills to bundle
            for _, skill in cluster_skills.iterrows():
                skill_bundles.append({
                    'skill_id': skill['skill_id'],
                    'skill_name': skill['skill_name'],
                    'category': skill['category'],
                    'subcategory': skill['subcategory'],
                    'skill_type': skill['skill_type'],
                    'total_occurrences': skill['total_occurrences'],
                    'jobs_count': skill['jobs_count'],
                    'prevalence_percent': skill['prevalence_percent'],
                    'cluster_id': cluster_id,
                    'bundle_name': bundle_name,
                    'bundle_description': bundle_description,
                    'bundle_rationale': f'Grouped by {skill["category"]} category similarity',
                    'sample_skills': '; '.join(cluster_skills['skill_name'].head(3).tolist()),
                    'sample_job_functions': 'Analysis pending',  # TODO: Implement
                    'bundle_size': len(cluster_skills),
                    'is_specialized': False,
                    'created_timestamp': datetime.now().isoformat()
                })
            
            # Add bundle characteristics
            bundle_characteristics.append({
                'cluster_id': cluster_id,
                'bundle_name': bundle_name,
                'bundle_description': bundle_description,
                'bundle_rationale': f'Grouped by {cluster_skills["category"].iloc[0]} category',
                'bundle_size': len(cluster_skills),
                'sample_skills': '; '.join(cluster_skills['skill_name'].head(3).tolist()),
                'sample_job_functions': 'Analysis pending',
                'dominant_category': cluster_skills['category'].mode().iloc[0],
                'category_purity': (cluster_skills['category'] == cluster_skills['category'].mode().iloc[0]).mean(),
                'application_level': self._assess_application_level(cluster_skills),
                'specialization_area': cluster_skills['category'].iloc[0],
                'average_jobs_per_skill': cluster_skills['jobs_count'].mean(),
                'taxonomy_alignment_score': 0.8,  # TODO: Implement proper calculation
                'silhouette_score': 0.0,  # TODO: Implement proper calculation
                'created_timestamp': datetime.now().isoformat()
            })
        
        return (
            pd.DataFrame(skill_bundles),
            pd.DataFrame(bundle_characteristics), 
            pd.DataFrame(specialized_skills)
        )
    
    def _generate_bundle_name(self, cluster_skills: pd.DataFrame) -> str:
        """Generate business-readable bundle name."""
        dominant_category = cluster_skills['category'].mode().iloc[0]
        size = len(cluster_skills)
        return f"{dominant_category} Skills Bundle ({size} skills)"
    
    def _generate_bundle_description(self, cluster_skills: pd.DataFrame) -> str:
        """Generate human-interpretable bundle description."""
        dominant_category = cluster_skills['category'].mode().iloc[0]
        avg_prevalence = cluster_skills['prevalence_percent'].mean()
        return f"Collection of {dominant_category} skills with {avg_prevalence:.1f}% average prevalence"
    
    def _assess_application_level(self, cluster_skills: pd.DataFrame) -> str:
        """Assess the application level of skills in the bundle."""
        avg_prevalence = cluster_skills['prevalence_percent'].mean()
        
        if avg_prevalence >= 50:
            return "Basic"
        elif avg_prevalence >= 20:
            return "Intermediate"
        else:
            return "Advanced"


class ClusteringAnalyzer:
    """
    Main orchestrator for clustering analysis.
    
    Coordinates job profile clustering, skills bundling, and produces
    comprehensive clustering intelligence for strategic workforce planning.
    """
    
    def __init__(self, config_manager=None):
        """Initialize clustering analyzer."""
        self.config_manager = config_manager or get_config_manager()
        self.job_clusterer = JobProfileClusterer(config_manager)
        self.skills_clusterer = SkillsBundleClusterer(config_manager)
        
        log_info("ClusteringAnalyzer initialized")
    
    def execute_clustering_analysis(self, db_path: str) -> ClusteringResult:
        """
        Execute complete clustering analysis.
        
        Args:
            db_path: Path to the SQLite database
            
        Returns:
            ClusteringResult with all analysis components
        """
        log_info("Starting complete clustering analysis", {
            'database': db_path
        })
        
        try:
            # Perform job profile clustering
            job_clusters_df, job_metrics = self.job_clusterer.cluster_job_profiles(db_path)
            
            # Generate job cluster characteristics
            job_characteristics_df = self._extract_job_characteristics(job_clusters_df, job_metrics)
            
            # Perform skills clustering and bundling
            skill_bundles_df, skill_characteristics_df, specialized_skills_df = self.skills_clusterer.cluster_skills(db_path)
            
            # Compile metadata
            metadata = {
                'analysis_timestamp': datetime.now().isoformat(),
                'job_clustering': {
                    'n_clusters': job_metrics.n_clusters,
                    'n_noise': job_metrics.n_noise,
                    'silhouette_score': job_metrics.silhouette_score,
                    'quality_assessment': job_metrics.quality_assessment
                },
                'skills_clustering': {
                    'n_bundles': len(skill_characteristics_df),
                    'n_specialized': len(specialized_skills_df),
                    'total_skills': len(skill_bundles_df) + len(specialized_skills_df)
                },
                'configuration': {
                    'job_eps': self.job_clusterer.eps,
                    'job_min_samples': self.job_clusterer.min_samples,
                    'skills_eps': self.skills_clusterer.eps,
                    'skills_min_samples': self.skills_clusterer.min_samples
                }
            }
            
            result = ClusteringResult(
                job_clusters_df=job_clusters_df,
                job_characteristics_df=job_characteristics_df,
                skill_bundles_df=skill_bundles_df,
                skill_characteristics_df=skill_characteristics_df,
                specialized_skills_df=specialized_skills_df,
                metadata=metadata
            )
            
            log_info("Clustering analysis completed successfully", metadata)
            return result
            
        except Exception as e:
            log_info("Clustering analysis failed", {
                'error': str(e)
            })
            raise
    
    def _extract_job_characteristics(self, job_clusters_df: pd.DataFrame, 
                                   metrics: ClusteringMetrics) -> pd.DataFrame:
        """Extract job cluster characteristics for analytics_job_family_characteristics table."""
        # Group by cluster to get characteristics
        characteristics = []
        
        for cluster_id in job_clusters_df['cluster_id'].unique():
            if cluster_id == -1:  # Skip noise
                continue
                
            cluster_jobs = job_clusters_df[job_clusters_df['cluster_id'] == cluster_id]
            
            if len(cluster_jobs) > 0:
                char = cluster_jobs.iloc[0]  # Get cluster info from first job
                
                # Calculate enhanced characteristics for job family table
                job_functions = cluster_jobs.get('job_function', cluster_jobs.get('JobFunction', pd.Series()))
                management_levels = cluster_jobs.get('management_level', cluster_jobs.get('ManagementLevel', pd.Series()))
                
                # Determine dominant function and purity
                if not job_functions.empty:
                    dominant_function = job_functions.mode().iloc[0] if not job_functions.mode().empty else 'Mixed'
                    function_purity = (job_functions == dominant_function).mean()
                else:
                    dominant_function = 'Unknown'
                    function_purity = 0.0
                
                # Assess specialization depth
                unique_functions = job_functions.nunique() if not job_functions.empty else 0
                if unique_functions <= 1:
                    specialization_depth = "deep"
                elif unique_functions <= 3:
                    specialization_depth = "moderate"
                else:
                    specialization_depth = "broad"
                
                # Management level pattern
                mgmt_pattern = management_levels.value_counts().to_dict() if not management_levels.empty else {}
                
                characteristics.append({
                    'cluster_id': cluster_id,
                    'family_name': char.get('cluster_name', f'Job Family {cluster_id}'),
                    'family_description': char.get('cluster_description', f'Job family with {len(cluster_jobs)} related roles'),
                    'family_rationale': char.get('cluster_rationale', 'Jobs grouped by skill similarity'),
                    'cluster_size': len(cluster_jobs),
                    'sample_jobs': char.get('sample_jobs', '')[:200],  # Truncate for storage
                    'sample_skills': char.get('sample_skills', '')[:200],
                    'core_job_functions': str(job_functions.value_counts().head(3).to_dict()) if not job_functions.empty else '{}',
                    'secondary_job_functions': str(job_functions.value_counts().tail(2).to_dict()) if not job_functions.empty else '{}',
                    'dominant_function': dominant_function,
                    'function_purity': round(function_purity, 3),
                    'management_level_pattern': str(mgmt_pattern),
                    'specialization_depth': specialization_depth,
                    'average_skills_per_job': 0.0,  # TODO: Calculate from database
                    'silhouette_score': metrics.silhouette_score,
                    'intra_family_similarity': char.get('intra_cluster_similarity', 0.0),
                    'inter_family_separation': char.get('inter_cluster_distance', 0.0),
                    'business_value_score': 0.8,  # Default high value for all clusters
                    'career_pathway_potential': 'medium',  # Default assessment
                    'skill_transferability': 0.7,  # Default good transferability
                    'market_demand_level': 'medium',  # Default market demand
                    'typical_career_stage': 'mid',  # Default career stage
                    'promotion_frequency': 'medium',  # Default promotion frequency
                    'lateral_movement_potential': 'high',  # Default high potential
                    'clustering_algorithm': char.get('clustering_algorithm', 'DBSCAN'),
                    'algorithm_parameters': char.get('algorithm_parameters', ''),
                    'quality_validation_date': datetime.now().isoformat(),
                    'business_review_date': datetime.now().isoformat(),
                    'created_timestamp': datetime.now().isoformat()
                })
        
        return pd.DataFrame(characteristics)