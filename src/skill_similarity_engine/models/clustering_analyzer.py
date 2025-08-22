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
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Set, Any, Union
from collections import defaultdict, Counter
from dataclasses import dataclass

# Import calculation error classes for fail-fast implementation
from ..errors.calculation_errors import CalculationError, ConfigurationError, DataQualityError, BusinessLogicError

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
            float(silhouette), n_clusters, n_noise, len(cluster_labels), cluster_sizes
        )
        
        return ClusteringMetrics(
            silhouette_score=float(silhouette),
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
        clustered_skills, cluster_silhouette_scores = self._perform_skills_clustering(skills_data)
        
        # Generate skill bundles
        skill_bundles_df, bundle_characteristics_df, specialized_skills_df = self._generate_skill_bundles(
            clustered_skills, cluster_silhouette_scores, db_path
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
    
    def _perform_skills_clustering(self, skills_data: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[int, float]]:
        """Perform DBSCAN clustering on skills data and calculate silhouette scores."""
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
        
        # Calculate silhouette scores per cluster
        cluster_silhouette_scores = self._calculate_cluster_silhouette_scores(skills_with_clusters)
        
        return skills_with_clusters, cluster_silhouette_scores
    
    def _calculate_cluster_silhouette_scores(self, clustered_skills: pd.DataFrame) -> Dict[int, float]:
        """Calculate silhouette scores for each cluster based on skill features."""
        cluster_silhouette_scores = {}
        
        # Get unique cluster IDs (excluding noise)
        unique_clusters = clustered_skills['cluster_id'].unique()
        valid_clusters = [c for c in unique_clusters if c != -1]
        
        if len(valid_clusters) < 2:
            # Need at least 2 clusters for silhouette score
            for cluster_id in valid_clusters:
                cluster_silhouette_scores[cluster_id] = 0.5  # Default moderate score
            return cluster_silhouette_scores
        
        try:
            # Create feature matrix based on skill characteristics
            # Using prevalence_percent and jobs_count as features for similarity
            features = clustered_skills[['prevalence_percent', 'jobs_count']].values
            
            # Standardize features for better silhouette calculation
            from sklearn.preprocessing import StandardScaler
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(features)
            
            # Calculate overall silhouette score
            cluster_labels = clustered_skills['cluster_id'].values
            overall_silhouette = silhouette_score(features_scaled, cluster_labels)
            
            # Calculate per-cluster silhouette scores
            silhouette_samples_scores = silhouette_samples(features_scaled, cluster_labels)
            
            for cluster_id in valid_clusters:
                cluster_mask = clustered_skills['cluster_id'] == cluster_id
                cluster_samples = silhouette_samples_scores[cluster_mask.values]
                cluster_silhouette_mean = float(np.mean(cluster_samples))
                cluster_silhouette_scores[cluster_id] = round(cluster_silhouette_mean, 3)
            
            log_info("Calculated cluster silhouette scores", {
                'overall_silhouette': round(overall_silhouette, 3),
                'n_clusters': len(valid_clusters),
                'cluster_scores': {k: v for k, v in cluster_silhouette_scores.items()}
            })
            
        except Exception as e:
            log_info("Failed to calculate silhouette scores, using defaults", {'error': str(e)})
            # Fallback to default scores based on cluster quality indicators
            for cluster_id in valid_clusters:
                cluster_skills = clustered_skills[clustered_skills['cluster_id'] == cluster_id]
                cluster_size = len(cluster_skills)
                category_purity = (cluster_skills['category'] == cluster_skills['category'].mode().iloc[0]).mean()
                
                # Estimate silhouette based on cluster quality
                if cluster_size >= 10 and category_purity >= 0.8:
                    estimated_silhouette = 0.7
                elif cluster_size >= 5 and category_purity >= 0.6:
                    estimated_silhouette = 0.5
                else:
                    estimated_silhouette = 0.3
                    
                cluster_silhouette_scores[cluster_id] = estimated_silhouette
        
        return cluster_silhouette_scores
    
    def _calculate_intra_bundle_similarity(self, cluster_skills: pd.DataFrame) -> float:
        """
        Calculate intra-bundle similarity - average similarity within the skill bundle.
        Uses prevalence and job count patterns to determine how cohesive the bundle is.
        """
        if len(cluster_skills) <= 1:
            return 1.0  # Single skill or empty bundle has perfect internal similarity
        
        try:
            # Create feature vectors for similarity calculation
            features = cluster_skills[['prevalence_percent', 'jobs_count']].values
            
            # Standardize features
            from sklearn.preprocessing import StandardScaler
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(features)
            
            # Calculate pairwise cosine similarities within the bundle
            similarity_matrix = cosine_similarity(features_scaled)
            
            # Get upper triangle of similarity matrix (excluding diagonal)
            n_skills = len(cluster_skills)
            upper_triangle_indices = np.triu_indices(n_skills, k=1)
            similarities = similarity_matrix[upper_triangle_indices]
            
            if len(similarities) == 0:
                return 1.0
            
            # Calculate average similarity
            intra_similarity = float(np.mean(similarities))
            
            # Apply category coherence bonus
            category_purity = (cluster_skills['category'] == cluster_skills['category'].mode().iloc[0]).mean()
            category_bonus = category_purity * 0.1  # Small bonus for category coherence
            
            final_similarity = min(1.0, intra_similarity + category_bonus)
            
            return round(final_similarity, 3)
            
        except Exception as e:
            log_info("Failed to calculate intra-bundle similarity, using fallback", {'error': str(e)})
            
            # Fallback: estimate based on category purity and size
            category_purity = (cluster_skills['category'] == cluster_skills['category'].mode().iloc[0]).mean()
            size_factor = min(1.0, 1.0 / (1 + len(cluster_skills) / 20))  # Smaller bundles more similar
            
            fallback_similarity = (0.7 * category_purity) + (0.3 * size_factor)
            return round(fallback_similarity, 3)
    
    def _calculate_inter_bundle_distance(self, current_cluster_skills: pd.DataFrame, all_clustered_skills: pd.DataFrame, current_cluster_id: int) -> float:
        """
        Calculate inter-bundle distance - average distance from current bundle to other bundles.
        Higher values indicate better separation from other skill bundles.
        """
        if len(current_cluster_skills) == 0:
            return 0.0
        
        try:
            # Get other clusters (excluding current and noise)
            other_clusters = all_clustered_skills[
                (all_clustered_skills['cluster_id'] != current_cluster_id) & 
                (all_clustered_skills['cluster_id'] != -1)
            ]
            
            if len(other_clusters) == 0:
                return 1.0  # Perfect separation if no other clusters
            
            # Calculate centroid of current cluster
            current_features = current_cluster_skills[['prevalence_percent', 'jobs_count']].values
            from sklearn.preprocessing import StandardScaler
            scaler = StandardScaler()
            current_features_scaled = scaler.fit_transform(current_features)
            current_centroid = np.mean(current_features_scaled, axis=0)
            
            # Calculate distances to other cluster centroids
            other_cluster_ids = other_clusters['cluster_id'].unique()
            distances_to_other_clusters = []
            
            for other_cluster_id in other_cluster_ids:
                other_cluster_skills = other_clusters[other_clusters['cluster_id'] == other_cluster_id]
                
                if len(other_cluster_skills) > 0:
                    # Calculate centroid of other cluster using the same scaler
                    other_features = other_cluster_skills[['prevalence_percent', 'jobs_count']].values
                    other_features_scaled = scaler.transform(other_features)
                    other_centroid = np.mean(other_features_scaled, axis=0)
                    
                    # Calculate Euclidean distance between centroids
                    distance = float(np.linalg.norm(current_centroid - other_centroid))
                    distances_to_other_clusters.append(distance)
            
            if not distances_to_other_clusters:
                return 1.0
            
            # Average distance to other clusters
            avg_inter_distance = float(np.mean(distances_to_other_clusters))
            
            # Apply category separation bonus
            current_categories = set(current_cluster_skills['category'].unique())
            other_categories = set(other_clusters['category'].unique())
            category_overlap = len(current_categories & other_categories) / len(current_categories | other_categories) if current_categories | other_categories else 0
            category_separation_bonus = (1 - category_overlap) * 0.2  # Bonus for distinct categories
            
            final_distance = min(1.0, avg_inter_distance + category_separation_bonus)
            
            return round(final_distance, 3)
            
        except Exception as e:
            log_info("Failed to calculate inter-bundle distance, using fallback", {'error': str(e)})
            
            # Fallback: estimate based on cluster size and category uniqueness
            current_categories = set(current_cluster_skills['category'].unique())
            other_clusters = all_clustered_skills[
                (all_clustered_skills['cluster_id'] != current_cluster_id) & 
                (all_clustered_skills['cluster_id'] != -1)
            ]
            
            if len(other_clusters) == 0:
                return 1.0
            
            other_categories = set(other_clusters['category'].unique())
            category_uniqueness = 1 - (len(current_categories & other_categories) / len(current_categories | other_categories)) if current_categories | other_categories else 0.5
            
            # Size factor - smaller clusters typically more distinct
            size_factor = min(1.0, 1.0 / (1 + len(current_cluster_skills) / 50))
            
            fallback_distance = (0.6 * category_uniqueness) + (0.4 * size_factor)
            return round(fallback_distance, 3)
    
    def _calculate_taxonomy_alignment_score(self, cluster_skills: pd.DataFrame) -> float:
        """
        Calculate taxonomy alignment score - how well the skills in this bundle align with taxonomy categories.
        Higher scores indicate better adherence to the existing skill taxonomy structure.
        """
        if len(cluster_skills) == 0:
            return 0.0
        
        try:
            # Factor 1: Category purity (40% weight)
            category_purity = (cluster_skills['category'] == cluster_skills['category'].mode().iloc[0]).mean()
            
            # Factor 2: Subcategory consistency (30% weight)
            if 'subcategory' in cluster_skills.columns:
                subcategory_purity = (cluster_skills['subcategory'] == cluster_skills['subcategory'].mode().iloc[0]).mean()
            else:
                subcategory_purity = 1.0  # Assume perfect if no subcategory data
            
            # Factor 3: Skill type consistency (20% weight)
            if 'skill_type' in cluster_skills.columns:
                skill_type_purity = (cluster_skills['skill_type'] == cluster_skills['skill_type'].mode().iloc[0]).mean()
            else:
                skill_type_purity = 1.0  # Assume perfect if no skill type data
            
            # Factor 4: Bundle size appropriateness (10% weight)
            bundle_size = len(cluster_skills)
            if 5 <= bundle_size <= 50:
                size_score = 1.0  # Optimal size range
            elif bundle_size < 5:
                size_score = bundle_size / 5.0  # Penalty for very small bundles
            else:
                size_score = max(0.3, 1.0 - ((bundle_size - 50) / 100.0))  # Penalty for very large bundles
            
            # Calculate weighted taxonomy alignment score
            taxonomy_score = (
                0.4 * category_purity +
                0.3 * subcategory_purity +
                0.2 * skill_type_purity +
                0.1 * size_score
            )
            
            return round(taxonomy_score, 3)
            
        except Exception as e:
            log_info("Failed to calculate taxonomy alignment score, using fallback", {'error': str(e)})
            
            # Simple fallback based on category purity
            category_purity = (cluster_skills['category'] == cluster_skills['category'].mode().iloc[0]).mean()
            return round(category_purity * 0.8, 3)  # Conservative estimate
    
    def _get_sample_job_functions(self, cluster_skills: pd.DataFrame, db_path: str) -> str:
        """
        Get sample job functions that commonly use skills from this bundle.
        """
        try:
            skill_ids = cluster_skills['skill_id'].tolist()
            if not skill_ids:
                return "No job functions found"
            
            with sqlite3.connect(db_path) as conn:
                # Get job functions that use these skills
                placeholders = ','.join(['?' for _ in skill_ids])
                query = f"""
                SELECT 
                    jp.JobFunction,
                    COUNT(DISTINCT js.Skill_ID) as skills_used,
                    COUNT(DISTINCT js.JobProfileID) as jobs_count
                FROM core_job_skill_requirements js
                JOIN core_job_architecture jp ON js.JobProfileID = jp.JobProfileID
                WHERE js.Skill_ID IN ({placeholders})
                GROUP BY jp.JobFunction
                ORDER BY skills_used DESC, jobs_count DESC
                LIMIT 3
                """
                
                cursor = conn.execute(query, skill_ids)
                results = cursor.fetchall()
                
                if results:
                    job_functions = [row[0] for row in results if row[0]]
                    return '; '.join(job_functions)
                else:
                    return "General workforce functions"
                    
        except Exception as e:
            log_info("Failed to get sample job functions", {'error': str(e)})
            return "Analysis not available"
    
    def _calculate_intra_bundle_cohesion_or_fail(self, cluster_skills: pd.DataFrame, all_skills_similarity_matrix: Optional[np.ndarray] = None) -> float:
        """
        Calculate intra-bundle cohesion (average similarity within bundle).
        
        Args:
            cluster_skills: Skills in this bundle
            all_skills_similarity_matrix: Optional precomputed similarity matrix
            
        Returns:
            float: Average intra-cluster similarity (0.0-1.0)
            
        Raises:
            DataQualityError: If cluster data is insufficient
            CalculationError: If calculation fails
        """
        if len(cluster_skills) <= 1:
            return 1.0  # Single skill bundles have perfect cohesion
            
        try:
            # For now, estimate based on category purity and skill relationships
            # In a full implementation, this would use actual skill similarity matrix
            
            # Factor 1: Category purity (same category = more cohesive)
            category_purity = (cluster_skills['category'] == cluster_skills['category'].mode().iloc[0]).mean()
            
            # Factor 2: Jobs count variance (similar job counts = more cohesive)
            jobs_variance = cluster_skills['jobs_count'].var()
            max_jobs = cluster_skills['jobs_count'].max()
            variance_score = 1 - min(1.0, jobs_variance / (max_jobs ** 2)) if max_jobs > 0 else 0.5
            
            # Factor 3: Bundle size (smaller bundles tend to be more cohesive)
            size_factor = max(0.2, 1 - (len(cluster_skills) / 100))  # Penalty for very large bundles
            
            # Calculate weighted cohesion
            cohesion = (category_purity * 0.5) + (variance_score * 0.3) + (size_factor * 0.2)
            
            return round(cohesion, 3)
            
        except Exception as e:
            raise CalculationError(
                f"Intra-bundle cohesion calculation failed: {str(e)}",
                calculation_type="intra_bundle_cohesion",
                data_context={'cluster_size': len(cluster_skills)}
            ) from e

    def _calculate_inter_bundle_separation_or_fail(self, current_cluster_skills: pd.DataFrame, all_clustered_skills: pd.DataFrame, current_cluster_id: int) -> float:
        """
        Calculate inter-bundle separation (distance from other bundles).
        
        Args:
            current_cluster_skills: Skills in current bundle
            all_clustered_skills: All clustered skills with cluster assignments
            current_cluster_id: ID of current cluster
            
        Returns:
            float: Average separation from other clusters (0.0-1.0)
            
        Raises:
            DataQualityError: If cluster data is insufficient
            CalculationError: If calculation fails
        """
        if len(current_cluster_skills) == 0:
            raise DataQualityError(
                "Cannot calculate inter-bundle separation for empty cluster",
                data_issue="empty_cluster",
                required_conditions="cluster must have at least 1 skill"
            )
            
        try:
            # Get other clusters for comparison
            other_clusters = all_clustered_skills[
                (all_clustered_skills['cluster_id'] != current_cluster_id) & 
                (all_clustered_skills['cluster_id'] != -1)  # Exclude noise
            ]
            
            if len(other_clusters) == 0:
                return 1.0  # Only cluster = maximum separation
            
            # Factor 1: Category uniqueness (different categories = better separation)
            current_categories = set(current_cluster_skills['category'].unique())
            other_categories = set(other_clusters['category'].unique())
            category_uniqueness = 1 - (len(current_categories & other_categories) / len(current_categories | other_categories)) if current_categories | other_categories else 0.5
            
            # Factor 2: Jobs count range separation (different job counts = better separation)
            current_jobs_mean = current_cluster_skills['jobs_count'].mean()
            other_jobs_mean = other_clusters['jobs_count'].mean()
            jobs_diff = abs(current_jobs_mean - other_jobs_mean) / max(current_jobs_mean, other_jobs_mean, 1)
            jobs_separation = min(1.0, jobs_diff)
            
            # Factor 3: Size-based separation (different cluster sizes = better separation)
            current_size = len(current_cluster_skills)
            other_cluster_sizes = other_clusters.groupby('cluster_id').size()
            if len(other_cluster_sizes) > 0:
                avg_other_size = other_cluster_sizes.mean()
                size_diff = abs(current_size - avg_other_size) / max(current_size, avg_other_size, 1)
                size_separation = min(1.0, size_diff)
            else:
                size_separation = 1.0
            
            # Calculate weighted separation
            separation = (category_uniqueness * 0.5) + (jobs_separation * 0.3) + (size_separation * 0.2)
            
            return round(separation, 3)
            
        except Exception as e:
            raise CalculationError(
                f"Inter-bundle separation calculation failed: {str(e)}",
                calculation_type="inter_bundle_separation",
                data_context={'cluster_size': len(current_cluster_skills)}
            ) from e

    def _calculate_common_job_families_or_fail(self, cluster_skills: pd.DataFrame, db_path: str) -> str:
        """
        Calculate common job families for skills in this bundle.
        
        Args:
            cluster_skills: Skills in this bundle
            db_path: Path to database for job family lookup
            
        Returns:
            str: JSON string of common job families and their frequencies
            
        Raises:
            DataQualityError: If cluster data is insufficient
            CalculationError: If calculation fails
        """
        if len(cluster_skills) == 0:
            raise DataQualityError(
                "Cannot calculate common job families for empty cluster",
                data_issue="empty_cluster",
                required_conditions="cluster must have at least 1 skill"
            )
            
        try:
            import sqlite3
            import json
            
            with sqlite3.connect(db_path) as conn:
                # Get job families for skills in this bundle
                skill_ids = "', '".join(cluster_skills['skill_id'].tolist())
                query = f"""
                SELECT DISTINCT jf.JobFunction, COUNT(DISTINCT jsr.JobProfileID) as job_count
                FROM core_job_skill_requirements jsr
                JOIN core_job_architecture jf ON jsr.JobProfileID = jf.JobProfileID
                WHERE jsr.Skill_ID IN ('{skill_ids}')
                GROUP BY jf.JobFunction
                ORDER BY job_count DESC
                LIMIT 10
                """
                
                cursor = conn.execute(query)
                job_families = {}
                for row in cursor.fetchall():
                    job_function, count = row
                    job_families[job_function] = count
                
                if not job_families:
                    return json.dumps({"note": "No job families found for these skills"})
                
                return json.dumps(job_families)
                
        except Exception as e:
            raise CalculationError(
                f"Common job families calculation failed: {str(e)}",
                calculation_type="common_job_families",
                data_context={'cluster_size': len(cluster_skills)}
            ) from e

    def _calculate_typical_career_stage_bundle_or_fail(self, cluster_skills: pd.DataFrame, db_path: str) -> str:
        """
        Calculate typical career stage for skills in this bundle.
        
        Args:
            cluster_skills: Skills in this bundle
            db_path: Path to database for management level lookup
            
        Returns:
            str: 'early', 'mid', or 'senior' based on management levels
            
        Raises:
            DataQualityError: If cluster data is insufficient
            CalculationError: If calculation fails
        """
        if len(cluster_skills) == 0:
            raise DataQualityError(
                "Cannot calculate typical career stage for empty cluster",
                data_issue="empty_cluster",
                required_conditions="cluster must have at least 1 skill"
            )
            
        try:
            import sqlite3
            
            with sqlite3.connect(db_path) as conn:
                # Get management levels for jobs requiring these skills
                skill_ids = "', '".join(cluster_skills['skill_id'].tolist())
                query = f"""
                SELECT ja.ManagementLevel, COUNT(*) as level_count
                FROM core_job_skill_requirements jsr
                JOIN core_job_architecture ja ON jsr.JobProfileID = ja.JobProfileID
                WHERE jsr.Skill_ID IN ('{skill_ids}')
                    AND ja.ManagementLevel IS NOT NULL 
                    AND ja.ManagementLevel != ''
                GROUP BY ja.ManagementLevel
                ORDER BY level_count DESC
                """
                
                cursor = conn.execute(query)
                level_counts = {}
                total_count = 0
                
                for row in cursor.fetchall():
                    level, count = row
                    level_counts[level] = count
                    total_count += count
                
                if total_count == 0:
                    # Fallback based on skill characteristics
                    avg_jobs = cluster_skills['jobs_count'].mean()
                    if avg_jobs > 50:
                        return 'early'  # High prevalence = entry level
                    elif avg_jobs > 20:
                        return 'mid'
                    else:
                        return 'senior'  # Low prevalence = senior/specialized
                
                # Calculate stage score based on management levels
                stage_score = 0
                for level, count in level_counts.items():
                    weight = count / total_count
                    level_str = str(level).lower()
                    
                    # Map management levels to stage scores
                    if any(term in level_str for term in ['na', 'ungraded', '0', 'entry', 'grad']):
                        stage_score += weight * 1  # Early career
                    elif any(term in level_str for term in ['1', '2', '3', 'junior', 'associate']):
                        stage_score += weight * 1.5  # Early-mid career
                    elif any(term in level_str for term in ['4', '5', 'manager', 'senior']):
                        stage_score += weight * 2.5  # Mid-senior career
                    elif any(term in level_str for term in ['6', '7', '8', 'director', 'executive']):
                        stage_score += weight * 3  # Senior career
                    else:
                        stage_score += weight * 2  # Default mid
                
                # Convert to category
                if stage_score <= 1.3:
                    return 'early'
                elif stage_score <= 2.3:
                    return 'mid'
                else:
                    return 'senior'
                    
        except Exception as e:
            raise CalculationError(
                f"Typical career stage calculation failed: {str(e)}",
                calculation_type="typical_career_stage",
                data_context={'cluster_size': len(cluster_skills)}
            ) from e

    def _calculate_skill_acquisition_difficulty_or_fail(self, cluster_skills: pd.DataFrame) -> str:
        """
        Calculate skill acquisition difficulty assessment.
        
        Args:
            cluster_skills: Skills in this bundle
            
        Returns:
            str: 'low', 'medium', or 'high' difficulty assessment
            
        Raises:
            DataQualityError: If cluster data is insufficient
            CalculationError: If calculation fails
        """
        if len(cluster_skills) == 0:
            raise DataQualityError(
                "Cannot calculate skill acquisition difficulty for empty cluster",
                data_issue="empty_cluster",
                required_conditions="cluster must have at least 1 skill"
            )
            
        try:
            # Factor 1: Skill rarity (rarer skills = harder to acquire)
            avg_prevalence = cluster_skills['prevalence_percent'].mean()
            if avg_prevalence > 20:
                rarity_score = 0.2  # Common skills = easier
            elif avg_prevalence > 5:
                rarity_score = 0.5  # Moderate prevalence = medium
            else:
                rarity_score = 1.0  # Rare skills = harder
            
            # Factor 2: Category complexity
            dominant_category = cluster_skills['category'].mode().iloc[0] if len(cluster_skills) > 0 else ''
            
            # Map categories to complexity
            high_complexity_categories = [
                'Information Technology', 'Engineering', 'Data Science', 
                'Finance', 'Analysis', 'Science'
            ]
            medium_complexity_categories = [
                'Business', 'Management', 'Sales', 'Marketing'
            ]
            
            if dominant_category in high_complexity_categories:
                category_score = 1.0
            elif dominant_category in medium_complexity_categories:
                category_score = 0.6
            else:
                category_score = 0.3
            
            # Factor 3: Bundle size (larger bundles = more complex to master all)
            bundle_size = len(cluster_skills)
            if bundle_size > 50:
                size_score = 1.0
            elif bundle_size > 20:
                size_score = 0.7
            else:
                size_score = 0.4
            
            # Calculate weighted difficulty
            difficulty_score = (rarity_score * 0.4) + (category_score * 0.4) + (size_score * 0.2)
            
            # Convert to category
            if difficulty_score >= 0.7:
                return 'high'
            elif difficulty_score >= 0.4:
                return 'medium'
            else:
                return 'low'
                
        except Exception as e:
            raise CalculationError(
                f"Skill acquisition difficulty calculation failed: {str(e)}",
                calculation_type="skill_acquisition_difficulty",
                data_context={'cluster_size': len(cluster_skills)}
            ) from e

    def _generate_skill_bundles(self, clustered_skills: pd.DataFrame, cluster_silhouette_scores: Dict[int, float], db_path: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Generate skill bundles, characteristics, and identify specialized skills."""
        skill_bundles = []
        bundle_characteristics = []
        specialized_skills = []
        
        # Identify specialized skills based on multiple criteria
        specialized_skills = self._identify_specialized_skills(clustered_skills)
        
        # Process each cluster
        for cluster_id in clustered_skills['cluster_id'].unique():
            cluster_skills = clustered_skills[clustered_skills['cluster_id'] == cluster_id]
            
            if cluster_id == -1:
                # Skip noise points - they're already handled in specialized skills
                continue
            
            # Generate bundle for this cluster
            bundle_name = self._generate_bundle_name(cluster_skills)
            bundle_description = self._generate_bundle_description(cluster_skills)
            
            # Calculate cluster-level metrics once per cluster
            bundle_confidence = self._calculate_bundle_confidence(cluster_skills)
            cluster_silhouette = cluster_silhouette_scores.get(cluster_id, 0.0)
            intra_bundle_similarity = self._calculate_intra_bundle_similarity(cluster_skills)
            inter_bundle_distance = self._calculate_inter_bundle_distance(cluster_skills, clustered_skills, cluster_id)
            taxonomy_alignment = self._calculate_taxonomy_alignment_score(cluster_skills)
            sample_job_functions = self._get_sample_job_functions(cluster_skills, db_path)
            
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
                    'sample_job_functions': sample_job_functions,
                    'bundle_size': len(cluster_skills),
                    'is_specialized': False,
                    'bundle_confidence': bundle_confidence,
                    'silhouette_score': cluster_silhouette,
                    'intra_bundle_similarity': intra_bundle_similarity,
                    'inter_bundle_distance': inter_bundle_distance,
                    'clustering_algorithm': self.algorithm,
                    'similarity_method': self.similarity_measure,
                    'algorithm_parameters': self._get_algorithm_parameters_string(),
                    'created_timestamp': datetime.now().isoformat()
                })
            
            # Identify core and peripheral skills
            core_skills, peripheral_skills = self._identify_core_peripheral_skills(cluster_skills)
            
            # Calculate business value score
            business_value_score = self._calculate_business_value_score(cluster_skills)
            
            # Assess training feasibility
            training_feasibility = self._assess_training_feasibility(cluster_skills)
            
            # Calculate skill complementarity
            skill_complementarity = self._calculate_skill_complementarity(cluster_skills)
            
            # Assess market demand level
            market_demand_level = self._assess_market_demand_level(cluster_skills, db_path)
            
            # Calculate the missing bundle intelligence fields using our new methods
            intra_cohesion = self._calculate_intra_bundle_cohesion_or_fail(cluster_skills)
            inter_separation = self._calculate_inter_bundle_separation_or_fail(cluster_skills, clustered_skills, cluster_id)
            common_job_families = self._calculate_common_job_families_or_fail(cluster_skills, db_path)
            typical_career_stage = self._calculate_typical_career_stage_bundle_or_fail(cluster_skills, db_path)
            skill_difficulty = self._calculate_skill_acquisition_difficulty_or_fail(cluster_skills)
            
            # Add bundle characteristics with all missing fields now calculated
            bundle_characteristics.append({
                'cluster_id': cluster_id,
                'bundle_name': bundle_name,
                'bundle_description': bundle_description,
                'bundle_rationale': f'Grouped by {cluster_skills["category"].iloc[0]} category',
                'bundle_size': len(cluster_skills),
                'sample_skills': '; '.join(cluster_skills['skill_name'].head(3).tolist()),
                'sample_job_functions': sample_job_functions,
                'core_skills': '; '.join(core_skills),
                'peripheral_skills': '; '.join(peripheral_skills),
                'dominant_category': cluster_skills['category'].mode().iloc[0],
                'category_purity': (cluster_skills['category'] == cluster_skills['category'].mode().iloc[0]).mean(),
                'application_level': self._assess_application_level(cluster_skills),
                'specialization_area': cluster_skills['category'].iloc[0],
                'average_jobs_per_skill': cluster_skills['jobs_count'].mean(),
                'taxonomy_alignment_score': taxonomy_alignment,
                'intra_bundle_cohesion': intra_cohesion,              # ✅ NOW CALCULATED
                'inter_bundle_separation': inter_separation,          # ✅ NOW CALCULATED
                'business_value_score': business_value_score,
                'training_feasibility': training_feasibility,
                'skill_complementarity': skill_complementarity,
                'market_demand_level': market_demand_level,
                'common_job_families': common_job_families,           # ✅ NOW CALCULATED
                'typical_career_stage': typical_career_stage,         # ✅ NOW CALCULATED
                'skill_acquisition_difficulty': skill_difficulty,    # ✅ NOW CALCULATED
                'silhouette_score': cluster_silhouette_scores.get(cluster_id, 0.0),
                'clustering_algorithm': self.algorithm,
                'algorithm_parameters': self._get_algorithm_parameters_string(),
                'quality_validation_date': datetime.now().isoformat(),  # ✅ NOW POPULATED
                'business_review_date': datetime.now().isoformat(),     # ✅ NOW POPULATED
                'created_timestamp': datetime.now().isoformat()
            })
        
        return (
            pd.DataFrame(skill_bundles),
            pd.DataFrame(bundle_characteristics), 
            pd.DataFrame(specialized_skills)
        )
    
    def _identify_specialized_skills(self, clustered_skills: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Identify specialized skills based on multiple strategic criteria.
        
        Specialized skills are those that:
        - Have <1% prevalence (very rare/unique)
        - Are in noise cluster (DBSCAN outliers)
        - Have high strategic value (emerging/critical)
        - Are unsuitable for bundling (too unique)
        """
        specialized_skills = []
        
        # Calculate total jobs for prevalence calculations
        total_jobs = clustered_skills['jobs_count'].max() if len(clustered_skills) > 0 else 1
        
        for _, skill in clustered_skills.iterrows():
            specialization_reasons = []
            is_specialized = False
            
            # Criterion 1: Very low prevalence (<1%)
            if skill['prevalence_percent'] < 1.0:
                specialization_reasons.append("Very low prevalence (<1%)")
                is_specialized = True
            
            # Criterion 2: Clustering outlier (noise points)
            if skill['cluster_id'] == -1:
                specialization_reasons.append("Clustering outlier - unique skill profile")
                is_specialized = True
            
            # Criterion 3: Low job count but high value indicators
            if skill['jobs_count'] < self.min_specialization_threshold:
                # Check for emerging/strategic skills
                if any(keyword in skill['skill_name'].lower() for keyword in 
                       ['ai', 'machine learning', 'blockchain', 'quantum', 'cloud', 'devops', 'cybersecurity']):
                    specialization_reasons.append("Emerging technology - strategic individual attention required")
                    is_specialized = True
                else:
                    specialization_reasons.append("Low prevalence - highly specialized")
                    is_specialized = True
            
            # Criterion 4: Skills in small clusters that should remain individual
            elif skill['cluster_id'] != -1:
                cluster_size = len(clustered_skills[clustered_skills['cluster_id'] == skill['cluster_id']])
                if cluster_size <= 2 and skill['prevalence_percent'] < 5.0:
                    specialization_reasons.append("Small cluster with unique characteristics")
                    is_specialized = True
            
            # Add to specialized skills if any criteria met
            if is_specialized:
                # Calculate specialization score (0-100 based on rarity and criteria)
                specialization_score = min(100.0, (100.0 - skill['prevalence_percent']) * 1.2)
                
                # Determine strategic importance
                strategic_importance = 'High' if any('emerging' in reason.lower() or 'strategic' in reason.lower() 
                                                   for reason in specialization_reasons) else 'Medium'
                
                # Determine specialization category
                if skill['prevalence_percent'] < 1.0:
                    spec_category = 'Ultra-Rare'
                elif skill['cluster_id'] == -1:
                    spec_category = 'Unique'
                elif any('emerging' in reason.lower() for reason in specialization_reasons):
                    spec_category = 'Emerging'
                else:
                    spec_category = 'Specialized'
                
                specialized_skills.append({
                    'skill_id': skill['skill_id'],
                    'skill_name': skill['skill_name'],
                    'category': skill['category'],
                    'subcategory': skill['subcategory'],
                    'skill_type': skill['skill_type'],
                    'jobs_count': skill['jobs_count'],
                    'prevalence_percent': skill['prevalence_percent'],
                    'specialization_score': specialization_score,
                    'rarity_rank': None,  # To be calculated in post-processing
                    'specialization_reason': '; '.join(specialization_reasons),
                    'specialization_category': spec_category,
                    'market_context': 'Internal analysis',
                    'strategic_importance': strategic_importance,
                    'skill_lifecycle_stage': 'Emerging' if 'emerging' in '; '.join(specialization_reasons).lower() else 'Mature',
                    'investment_recommendation': 'Individual development' if strategic_importance == 'High' else 'Monitor',
                    'related_skills': None,  # TODO: Implement skill relationship analysis
                    'typical_job_functions': None,  # TODO: Implement job function analysis
                    'training_availability': 'Limited' if specialization_score > 95 else 'Available',
                    'external_market_demand': 'High' if strategic_importance == 'High' else 'Moderate',
                    'analysis_methodology': 'Multi-criteria specialization analysis',
                    'confidence_level': 'High' if len(specialization_reasons) > 1 else 'Medium',
                    'last_review_date': datetime.now().isoformat(),
                    'next_review_date': (datetime.now() + timedelta(days=90)).isoformat(),
                    'created_timestamp': datetime.now().isoformat()
                })
        
        return specialized_skills
    
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
    
    def _get_algorithm_parameters_string(self) -> str:
        """Get algorithm-specific parameters as a string for metadata."""
        if self.algorithm == 'dbscan':
            return f"eps={self.eps}, min_samples={self.min_samples}"
        elif self.algorithm == 'hierarchical':
            return f"n_clusters={self.n_clusters}, linkage={self.linkage}"
        elif self.algorithm == 'kmeans':
            return f"n_clusters={self.n_clusters}, random_state=42"
        else:
            return f"algorithm={self.algorithm}"
    
    def _identify_core_peripheral_skills(self, cluster_skills: pd.DataFrame) -> Tuple[List[str], List[str]]:
        """
        Identify core and peripheral skills within a bundle based on prevalence and job usage.
        
        Core skills: Top 30% by combined prevalence and job count
        Peripheral skills: Bottom 30% by combined prevalence and job count
        Standard skills: Middle 40% (not categorized as core or peripheral)
        
        Args:
            cluster_skills: DataFrame with skills in the cluster
            
        Returns:
            Tuple of (core_skills_list, peripheral_skills_list)
        """
        if len(cluster_skills) == 0:
            return [], []
        
        # Calculate a composite score: prevalence (40%) + job usage (60%)
        cluster_skills = cluster_skills.copy()
        
        # Normalize prevalence and job counts to 0-1 scale within this cluster
        max_prevalence = cluster_skills['prevalence_percent'].max()
        max_jobs = cluster_skills['jobs_count'].max()
        
        # Avoid division by zero
        prevalence_norm = cluster_skills['prevalence_percent'] / max_prevalence if max_prevalence > 0 else 0
        jobs_norm = cluster_skills['jobs_count'] / max_jobs if max_jobs > 0 else 0
        
        # Composite score (job usage weighted higher as it indicates actual usage)
        cluster_skills['importance_score'] = (0.4 * prevalence_norm) + (0.6 * jobs_norm)
        
        # Sort by importance score
        sorted_skills = cluster_skills.sort_values('importance_score', ascending=False)
        
        # Calculate thresholds
        total_skills = len(sorted_skills)
        core_threshold = int(total_skills * 0.3)  # Top 30%
        peripheral_start = int(total_skills * 0.7)  # Bottom 30%
        
        # Ensure we have at least 1 skill in each category for larger bundles
        if total_skills >= 3:
            core_threshold = max(1, core_threshold)
            peripheral_start = min(total_skills - 1, peripheral_start)
        else:
            # For very small bundles, just return empty lists
            return [], []
        
        # Extract core and peripheral skills
        core_skills = sorted_skills.head(core_threshold)['skill_name'].tolist()
        peripheral_skills = sorted_skills.tail(total_skills - peripheral_start)['skill_name'].tolist()
        
        return core_skills, peripheral_skills
    
    def _calculate_business_value_score(self, cluster_skills: pd.DataFrame) -> float:
        """
        Calculate business value score for a skill bundle using multi-factor approach.
        
        Factors:
        - Prevalence factor (30%): Higher prevalence indicates broader applicability
        - Rarity balance factor (40%): Optimal value for skills that are neither too common nor too rare
        - Bundle cohesion factor (30%): Larger, well-formed bundles have higher training value
        
        Args:
            cluster_skills: DataFrame with skills in the cluster
            
        Returns:
            Business value score (0.0 to 1.0)
        """
        if len(cluster_skills) == 0:
            return 0.0
        
        # Factor 1: Prevalence factor (30% weight)
        # Higher average prevalence = higher business value (more widely applicable)
        avg_prevalence = cluster_skills['prevalence_percent'].mean()
        prevalence_factor = min(avg_prevalence / 100.0, 1.0)  # Normalize to 0-1
        
        # Factor 2: Rarity balance factor (40% weight)
        # Sweet spot is skills that are not too common (>80%) or too rare (<5%)
        # Bell curve with peak around 20-40% prevalence
        rarity_scores = []
        for prevalence in cluster_skills['prevalence_percent']:
            if prevalence < 5:  # Too rare
                rarity_score = prevalence / 5.0  # 0.0 to 1.0
            elif prevalence > 80:  # Too common
                rarity_score = (100 - prevalence) / 20.0  # 1.0 to 0.0
            else:  # Sweet spot (5-80%)
                # Peak at 30% prevalence
                if prevalence <= 30:
                    rarity_score = prevalence / 30.0  # 0.17 to 1.0
                else:
                    rarity_score = 1.0 - ((prevalence - 30) / 50.0)  # 1.0 to 0.0
            rarity_scores.append(min(max(rarity_score, 0.0), 1.0))
        
        rarity_balance_factor = np.mean(rarity_scores)
        
        # Factor 3: Bundle cohesion factor (30% weight)
        # Larger bundles with consistent job usage = higher training value
        bundle_size = len(cluster_skills)
        avg_jobs_per_skill = cluster_skills['jobs_count'].mean()
        
        # Size score: optimal around 10-50 skills (too small = incomplete, too large = unwieldy)
        if bundle_size < 5:
            size_score = bundle_size / 5.0
        elif bundle_size <= 50:
            size_score = 1.0
        else:
            size_score = max(0.5, 1.0 - ((bundle_size - 50) / 100.0))  # Diminishing returns
        
        # Usage consistency score: higher average jobs per skill = more practical value
        # Normalize based on reasonable job counts (1-500 jobs per skill)
        usage_score = min(avg_jobs_per_skill / 100.0, 1.0)
        
        cohesion_factor = (size_score + usage_score) / 2.0
        
        # Combine factors with weights
        business_value_score = (
            0.3 * prevalence_factor +
            0.4 * rarity_balance_factor +
            0.3 * cohesion_factor
        )
        
        return round(business_value_score, 3)
    
    def _assess_training_feasibility(self, cluster_skills: pd.DataFrame) -> str:
        """
        Assess training feasibility for a skill bundle based on complexity factors.
        
        Assessment factors:
        - Bundle size: Larger bundles are more complex to train
        - Skill diversity: Mixed categories are harder to coordinate training
        - Prevalence accessibility: Common skills have more training resources available
        - Specialization level: Highly specialized skills are harder to train
        
        Args:
            cluster_skills: DataFrame with skills in the cluster
            
        Returns:
            Training feasibility level: "high", "medium", or "low"
        """
        if len(cluster_skills) == 0:
            return "low"
        
        # Factor 1: Bundle size complexity
        bundle_size = len(cluster_skills)
        if bundle_size <= 5:
            size_feasibility = 1.0  # Very manageable
        elif bundle_size <= 15:
            size_feasibility = 0.8  # Good size
        elif bundle_size <= 30:
            size_feasibility = 0.6  # Moderate complexity
        elif bundle_size <= 50:
            size_feasibility = 0.4  # Complex but doable
        else:
            size_feasibility = 0.2  # Very complex
        
        # Factor 2: Category diversity (using existing category_purity calculation)
        category_purity = (cluster_skills['category'] == cluster_skills['category'].mode().iloc[0]).mean()
        diversity_feasibility = category_purity  # Higher purity = easier to train together
        
        # Factor 3: Prevalence accessibility
        avg_prevalence = cluster_skills['prevalence_percent'].mean()
        if avg_prevalence >= 40:
            prevalence_feasibility = 1.0  # Common skills, lots of training available
        elif avg_prevalence >= 20:
            prevalence_feasibility = 0.8  # Moderate availability
        elif avg_prevalence >= 10:
            prevalence_feasibility = 0.6  # Some training available
        elif avg_prevalence >= 5:
            prevalence_feasibility = 0.4  # Limited training available
        else:
            prevalence_feasibility = 0.2  # Very limited training resources
        
        # Factor 4: Specialization level (based on average jobs per skill)
        avg_jobs_per_skill = cluster_skills['jobs_count'].mean()
        if avg_jobs_per_skill >= 100:
            specialization_feasibility = 1.0  # Widely used, easier to train
        elif avg_jobs_per_skill >= 50:
            specialization_feasibility = 0.8  # Good usage
        elif avg_jobs_per_skill >= 20:
            specialization_feasibility = 0.6  # Moderate usage
        elif avg_jobs_per_skill >= 10:
            specialization_feasibility = 0.4  # Limited usage
        else:
            specialization_feasibility = 0.2  # Highly specialized
        
        # Weighted combination (size and diversity matter most for training coordination)
        training_feasibility_score = (
            0.35 * size_feasibility +           # Bundle size impact
            0.25 * diversity_feasibility +      # Category coherence
            0.25 * prevalence_feasibility +     # Training resource availability
            0.15 * specialization_feasibility   # Specialization level
        )
        
        # Convert to categorical assessment
        if training_feasibility_score >= 0.7:
            return "high"
        elif training_feasibility_score >= 0.4:
            return "medium"
        else:
            return "low"
    
    def _calculate_skill_complementarity(self, cluster_skills: pd.DataFrame) -> float:
        """
        Calculate skill complementarity score - how well skills work together within bundle.
        
        Complementarity factors:
        - Category coherence: Skills from same category naturally complement
        - Usage pattern consistency: Skills used in similar job contexts work well together
        - Prevalence diversity: Mix of common foundation + specialized skills is optimal
        
        Args:
            cluster_skills: DataFrame with skills in the cluster
            
        Returns:
            Complementarity score (0.0 to 1.0)
        """
        if len(cluster_skills) == 0:
            return 0.0
        
        # Factor 1: Category coherence (40% weight)
        # Higher category purity = better natural complementarity
        category_purity = (cluster_skills['category'] == cluster_skills['category'].mode().iloc[0]).mean()
        coherence_score = category_purity
        
        # Factor 2: Usage pattern consistency (30% weight)
        # Skills with similar job usage patterns complement well
        job_counts = cluster_skills['jobs_count']
        if len(job_counts) > 1 and job_counts.std() > 0:
            # Lower coefficient of variation = more consistent usage patterns
            cv = job_counts.std() / job_counts.mean()
            consistency_score = max(0.0, 1.0 - min(cv / 2.0, 1.0))  # Normalize CV to 0-1
        else:
            consistency_score = 1.0  # Perfect consistency if all same or single skill
            
        # Factor 3: Prevalence diversity balance (30% weight) 
        # Optimal mix: some foundational skills (high prevalence) + some specialized (low prevalence)
        prevalences = cluster_skills['prevalence_percent']
        
        # Check for good diversity (some high, some low prevalence skills)
        high_prevalence_skills = (prevalences >= 30).sum()
        medium_prevalence_skills = ((prevalences >= 10) & (prevalences < 30)).sum()
        low_prevalence_skills = (prevalences < 10).sum()
        
        total_skills = len(prevalences)
        
        # Optimal distribution: 40% high, 40% medium, 20% low prevalence
        high_ratio = high_prevalence_skills / total_skills
        medium_ratio = medium_prevalence_skills / total_skills
        low_ratio = low_prevalence_skills / total_skills
        
        # Score based on distance from optimal distribution
        optimal_high = 0.4
        optimal_medium = 0.4  
        optimal_low = 0.2
        
        diversity_distance = (
            abs(high_ratio - optimal_high) +
            abs(medium_ratio - optimal_medium) + 
            abs(low_ratio - optimal_low)
        ) / 2.0  # Normalize to 0-1
        
        diversity_score = max(0.0, 1.0 - diversity_distance)
        
        # Combine factors with weights
        complementarity_score = (
            0.4 * coherence_score +      # Category coherence
            0.3 * consistency_score +    # Usage pattern consistency
            0.3 * diversity_score        # Prevalence diversity balance
        )
        
        return round(complementarity_score, 3)
    
    def _assess_market_demand_level(self, cluster_skills: pd.DataFrame, db_path: str) -> str:
        """
        Assess market demand level for a skill bundle by integrating with velocity analysis data.
        
        Combines:
        - Velocity trends from analytics_skill_demand_trends table
        - Current prevalence levels 
        - Bundle composition for overall market assessment
        
        Args:
            cluster_skills: DataFrame with skills in the cluster
            db_path: Path to database for velocity lookup
            
        Returns:
            Market demand level: "high", "medium", or "low"
        """
        if len(cluster_skills) == 0:
            return "low"
        
        try:
            with sqlite3.connect(db_path) as conn:
                # Get velocity data for skills in this bundle
                skill_ids = cluster_skills['skill_id'].tolist()
                placeholders = ','.join(['?' for _ in skill_ids])
                
                velocity_query = f"""
                SELECT skill_id, velocity_category, trend_direction, short_term_cagr, medium_term_cagr
                FROM analytics_skill_demand_trends 
                WHERE skill_id IN ({placeholders})
                """
                
                velocity_df = pd.read_sql_query(velocity_query, conn, params=skill_ids)
                
        except Exception as e:
            # If velocity data unavailable, fall back to prevalence-based assessment
            log_info(f"Velocity data unavailable, using prevalence fallback: {e}")
            velocity_df = pd.DataFrame()
        
        # Factor 1: Velocity trends (60% weight if available)
        if len(velocity_df) > 0:
            # Merge with cluster skills to get complete picture
            skills_with_velocity = cluster_skills.merge(
                velocity_df, on='skill_id', how='left'
            )
            
            # Score velocity trends
            velocity_scores = []
            for _, row in skills_with_velocity.iterrows():
                if pd.notna(row.get('velocity_category')):
                    velocity_cat = row['velocity_category']
                    if velocity_cat == 'accelerating':
                        velocity_scores.append(1.0)  # High demand
                    elif velocity_cat == 'growing':
                        velocity_scores.append(0.8)  # Good demand
                    elif velocity_cat == 'stable':
                        velocity_scores.append(0.6)  # Moderate demand
                    elif velocity_cat == 'declining':
                        velocity_scores.append(0.3)  # Low demand
                    else:
                        velocity_scores.append(0.5)  # Unknown/neutral
                else:
                    # No velocity data for this skill, use prevalence as proxy
                    prevalence = row['prevalence_percent']
                    if prevalence >= 40:
                        velocity_scores.append(0.7)  # High prevalence = likely demand
                    elif prevalence >= 20:
                        velocity_scores.append(0.6)  # Medium prevalence
                    else:
                        velocity_scores.append(0.4)  # Low prevalence
            
            velocity_factor = np.mean(velocity_scores) if velocity_scores else 0.5
            velocity_weight = 0.6
        else:
            # No velocity data available
            velocity_factor = 0.5  # Neutral
            velocity_weight = 0.0
        
        # Factor 2: Current prevalence levels (40% weight, or 100% if no velocity data)
        avg_prevalence = cluster_skills['prevalence_percent'].mean()
        if avg_prevalence >= 50:
            prevalence_factor = 0.9  # Very high demand (widely needed)
        elif avg_prevalence >= 30:
            prevalence_factor = 0.8  # High demand
        elif avg_prevalence >= 15:
            prevalence_factor = 0.6  # Moderate demand
        elif avg_prevalence >= 5:
            prevalence_factor = 0.4  # Lower demand
        else:
            prevalence_factor = 0.2  # Niche demand
        
        prevalence_weight = 1.0 - velocity_weight
        
        # Combine factors
        demand_score = (velocity_weight * velocity_factor) + (prevalence_weight * prevalence_factor)
        
        # Convert to categorical assessment
        if demand_score >= 0.7:
            return "high"
        elif demand_score >= 0.4:
            return "medium"
        else:
            return "low"
    
    def _calculate_bundle_confidence(self, cluster_skills: pd.DataFrame) -> float:
        """
        Calculate confidence score for skill bundle assignment.
        
        Confidence factors:
        - Cluster size stability: Optimal sizes are more reliable
        - Category purity: Taxonomically coherent clusters are more confident
        - Usage pattern consistency: Similar job usage indicates good clustering
        
        Args:
            cluster_skills: DataFrame with skills in the cluster
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        if len(cluster_skills) == 0:
            return 0.0
        
        # Factor 1: Cluster size stability (40% weight)
        # Optimal cluster sizes (5-50 skills) get highest confidence
        cluster_size = len(cluster_skills)
        if cluster_size < 3:
            size_confidence = 0.3  # Too small, likely noise
        elif cluster_size <= 10:
            size_confidence = 0.9  # Excellent size
        elif cluster_size <= 30:
            size_confidence = 1.0  # Optimal size
        elif cluster_size <= 50:
            size_confidence = 0.8  # Good size
        elif cluster_size <= 100:
            size_confidence = 0.6  # Large but manageable
        else:
            size_confidence = 0.4  # Too large, possibly overgeneralized
        
        # Factor 2: Category purity (35% weight)
        # Higher category purity = more confident clustering
        category_purity = (cluster_skills['category'] == cluster_skills['category'].mode().iloc[0]).mean()
        purity_confidence = category_purity
        
        # Factor 3: Usage pattern consistency (25% weight)
        # Skills with similar job usage patterns should cluster together
        job_counts = cluster_skills['jobs_count']
        if len(job_counts) > 1 and job_counts.std() > 0:
            # Lower coefficient of variation = more consistent = higher confidence
            cv = job_counts.std() / job_counts.mean()
            consistency_confidence = max(0.0, 1.0 - min(cv / 3.0, 1.0))  # Normalize CV
        else:
            consistency_confidence = 1.0  # Perfect consistency
        
        # Combine factors with weights
        bundle_confidence = (
            0.4 * size_confidence +        # Cluster size stability
            0.35 * purity_confidence +     # Category purity
            0.25 * consistency_confidence  # Usage pattern consistency
        )
        
        return round(bundle_confidence, 3)


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
    
    def _calculate_business_value_score_or_fail(self, cluster_jobs: pd.DataFrame, metrics: ClusteringMetrics) -> float:
        """
        Calculate actual business value score based on cluster quality and size.
        
        Factors:
        - Cluster quality (silhouette score): 40% weight
        - Cluster size/relevance: 30% weight  
        - Management level diversity: 30% weight
        
        Returns:
            float: Business value score (0.0-1.0)
            
        Raises:
            DataQualityError: If cluster data is insufficient
            CalculationError: If calculation fails
        """
        if len(cluster_jobs) == 0:
            raise DataQualityError(
                "Cannot calculate business value for empty cluster",
                data_issue="empty_cluster",
                required_conditions="cluster must have at least 1 job"
            )
        
        try:
            # Factor 1: Cluster quality (silhouette score) - 40% weight
            if metrics.silhouette_score is None:
                raise CalculationError(
                    "Missing silhouette score for business value calculation",
                    calculation_type="business_value",
                    data_context={'cluster_size': len(cluster_jobs)}
                )
            
            # Normalize silhouette score from [-1,1] to [0,1]
            quality_score = max(0, (metrics.silhouette_score + 1) / 2)
            
            # Factor 2: Cluster size relevance - 30% weight
            # Optimal size is 15-50 jobs (gets score of 1.0)
            cluster_size = len(cluster_jobs)
            if cluster_size >= 15 and cluster_size <= 50:
                size_score = 1.0
            elif cluster_size >= 5 and cluster_size <= 100:
                # Gradual penalty for too small or too large
                size_score = 0.8
            elif cluster_size >= 2:
                size_score = 0.6
            else:
                size_score = 0.3
            
            # Factor 3: Management level diversity - 30% weight
            management_levels = cluster_jobs.get('management_level', cluster_jobs.get('ManagementLevel', pd.Series()))
            if not management_levels.empty:
                unique_levels = len(management_levels.unique())
                # More diverse levels = more business value (cross-level skills)
                if unique_levels >= 4:
                    diversity_score = 1.0
                elif unique_levels >= 3:
                    diversity_score = 0.8
                elif unique_levels >= 2:
                    diversity_score = 0.6
                else:
                    diversity_score = 0.4
            else:
                # Missing management level data
                diversity_score = 0.5  # Neutral score
            
            # Calculate weighted business value score
            business_value = (
                quality_score * 0.4 +
                size_score * 0.3 +
                diversity_score * 0.3
            )
            
            return round(business_value, 3)
            
        except Exception as e:
            if isinstance(e, (DataQualityError, CalculationError)):
                raise
            
            raise CalculationError(
                f"Business value calculation failed: {str(e)}",
                calculation_type="business_value",
                data_context={
                    'cluster_size': len(cluster_jobs),
                    'silhouette_score': getattr(metrics, 'silhouette_score', None)
                }
            ) from e

    def _calculate_career_pathway_potential_or_fail(self, cluster_jobs: pd.DataFrame) -> str:
        """
        Calculate career pathway potential based on management level diversity and transitions.
        
        Returns:
            str: 'high', 'medium', or 'low' based on pathway opportunities
            
        Raises:
            DataQualityError: If cluster data is insufficient
            CalculationError: If calculation fails
        """
        if len(cluster_jobs) == 0:
            raise DataQualityError(
                "Cannot calculate career pathway potential for empty cluster",
                data_issue="empty_cluster",
                required_conditions="cluster must have at least 1 job"
            )
        
        try:
            # Factor 1: Management level diversity (more levels = more pathways)
            management_levels = cluster_jobs.get('management_level', cluster_jobs.get('ManagementLevel', pd.Series()))
            if not management_levels.empty:
                unique_levels = len(management_levels.unique())
                level_score = min(1.0, unique_levels / 4.0)  # Normalize to 0-1
            else:
                level_score = 0.5  # Neutral if no level data
            
            # Factor 2: Cluster size (larger clusters = more pathway options)
            cluster_size = len(cluster_jobs)
            if cluster_size >= 20:
                size_score = 1.0
            elif cluster_size >= 10:
                size_score = 0.8
            elif cluster_size >= 5:
                size_score = 0.6
            else:
                size_score = 0.4
            
            # Factor 3: Job function diversity (cross-functional opportunities)
            job_functions = cluster_jobs.get('job_function', cluster_jobs.get('JobFunction', pd.Series()))
            if not job_functions.empty:
                unique_functions = len(job_functions.unique())
                function_score = min(1.0, unique_functions / 3.0)  # Normalize to 0-1
            else:
                function_score = 0.5
            
            # Calculate weighted pathway potential
            pathway_score = (level_score * 0.4) + (size_score * 0.3) + (function_score * 0.3)
            
            # Categorize into high/medium/low
            if pathway_score >= 0.7:
                return 'high'
            elif pathway_score >= 0.4:
                return 'medium'
            else:
                return 'low'
                
        except Exception as e:
            if isinstance(e, (DataQualityError, CalculationError)):
                raise
            
            raise CalculationError(
                f"Career pathway potential calculation failed: {str(e)}",
                calculation_type="career_pathway_potential",
                data_context={'cluster_size': len(cluster_jobs)}
            ) from e

    def _calculate_skill_transferability_or_fail(self, cluster_jobs: pd.DataFrame) -> float:
        """
        Calculate skill transferability based on skill commonality and specialization.
        
        Returns:
            float: Transferability score (0.0-1.0)
            
        Raises:
            DataQualityError: If cluster data is insufficient
            CalculationError: If calculation fails
        """
        if len(cluster_jobs) == 0:
            raise DataQualityError(
                "Cannot calculate skill transferability for empty cluster",
                data_issue="empty_cluster",
                required_conditions="cluster must have at least 1 job"
            )
        
        try:
            # For now, estimate based on cluster cohesion and size
            # In a full implementation, this would analyze actual skill overlap
            
            cluster_size = len(cluster_jobs)
            
            # Factor 1: Cluster size (larger = more transferable skills)
            if cluster_size >= 15:
                size_factor = 0.8
            elif cluster_size >= 8:
                size_factor = 0.7
            elif cluster_size >= 3:
                size_factor = 0.6
            else:
                size_factor = 0.4
            
            # Factor 2: Management level spread (wider spread = more transferable)
            management_levels = cluster_jobs.get('management_level', cluster_jobs.get('ManagementLevel', pd.Series()))
            if not management_levels.empty:
                level_spread = len(management_levels.unique())
                level_factor = min(0.3, level_spread / 10)  # Max 0.3 contribution
            else:
                level_factor = 0.15  # Neutral
            
            # Factor 3: Function diversity (more functions = more transferable)
            job_functions = cluster_jobs.get('job_function', cluster_jobs.get('JobFunction', pd.Series()))
            if not job_functions.empty:
                function_diversity = len(job_functions.unique())
                function_factor = min(0.2, function_diversity / 5)  # Max 0.2 contribution
            else:
                function_factor = 0.1
            
            transferability = size_factor + level_factor + function_factor
            return round(min(1.0, transferability), 3)
            
        except Exception as e:
            if isinstance(e, (DataQualityError, CalculationError)):
                raise
            
            raise CalculationError(
                f"Skill transferability calculation failed: {str(e)}",
                calculation_type="skill_transferability",
                data_context={'cluster_size': len(cluster_jobs)}
            ) from e

    def _calculate_typical_career_stage_or_fail(self, cluster_jobs: pd.DataFrame) -> str:
        """
        Calculate typical career stage based on management level distribution.
        
        Returns:
            str: 'early', 'mid', or 'senior' based on management levels
            
        Raises:
            DataQualityError: If cluster data is insufficient
            CalculationError: If calculation fails
        """
        if len(cluster_jobs) == 0:
            raise DataQualityError(
                "Cannot calculate typical career stage for empty cluster",
                data_issue="empty_cluster",
                required_conditions="cluster must have at least 1 job"
            )
        
        try:
            management_levels = cluster_jobs.get('management_level', cluster_jobs.get('ManagementLevel', pd.Series()))
            
            if management_levels.empty:
                # No management level data - estimate from cluster characteristics
                cluster_size = len(cluster_jobs)
                if cluster_size <= 5:
                    return 'senior'  # Small specialized clusters often senior
                elif cluster_size <= 15:
                    return 'mid'
                else:
                    return 'early'  # Large clusters often entry-level
            
            # Analyze management level distribution
            level_counts = management_levels.value_counts()
            total_jobs = len(cluster_jobs)
            
            # Calculate weighted stage score
            stage_score = 0
            for level, count in level_counts.items():
                weight = count / total_jobs
                
                # Map levels to stage scores (customize based on your data)
                if any(term in str(level).lower() for term in ['graduate', 'junior', 'entry', 'analyst', 'associate']):
                    stage_score += weight * 1  # Early career
                elif any(term in str(level).lower() for term in ['senior', 'lead', 'principal', 'manager']):
                    stage_score += weight * 2  # Mid career
                elif any(term in str(level).lower() for term in ['director', 'executive', 'head', 'chief']):
                    stage_score += weight * 3  # Senior career
                else:
                    stage_score += weight * 2  # Default to mid career
            
            # Convert to category
            if stage_score <= 1.3:
                return 'early'
            elif stage_score <= 2.3:
                return 'mid'
            else:
                return 'senior'
                
        except Exception as e:
            if isinstance(e, (DataQualityError, CalculationError)):
                raise
            
            raise CalculationError(
                f"Typical career stage calculation failed: {str(e)}",
                calculation_type="typical_career_stage", 
                data_context={'cluster_size': len(cluster_jobs)}
            ) from e

    def _calculate_market_demand_level_or_fail(self, cluster_jobs: pd.DataFrame) -> str:
        """
        Calculate market demand level based on cluster size and job function diversity.
        
        Returns:
            str: 'high', 'medium', or 'low' based on market demand indicators
            
        Raises:
            DataQualityError: If cluster data is insufficient
            CalculationError: If calculation fails
        """
        if len(cluster_jobs) == 0:
            raise DataQualityError(
                "Cannot calculate market demand level for empty cluster",
                data_issue="empty_cluster",
                required_conditions="cluster must have at least 1 job"
            )
        
        try:
            cluster_size = len(cluster_jobs)
            
            # Factor 1: Cluster size (larger clusters suggest higher demand)
            if cluster_size >= 25:
                size_score = 1.0  # High demand
            elif cluster_size >= 12:
                size_score = 0.7  # Medium-high demand
            elif cluster_size >= 5:
                size_score = 0.5  # Medium demand
            else:
                size_score = 0.3  # Lower demand (specialized roles)
            
            # Factor 2: Function diversity (cross-functional = higher demand)
            job_functions = cluster_jobs.get('job_function', cluster_jobs.get('JobFunction', pd.Series()))
            if not job_functions.empty:
                function_diversity = len(job_functions.unique())
                diversity_boost = min(0.3, function_diversity / 10)
            else:
                diversity_boost = 0
            
            demand_score = size_score + diversity_boost
            
            # Categorize demand level
            if demand_score >= 0.8:
                return 'high'
            elif demand_score >= 0.5:
                return 'medium' 
            else:
                return 'low'
                
        except Exception as e:
            if isinstance(e, (DataQualityError, CalculationError)):
                raise
            
            raise CalculationError(
                f"Market demand level calculation failed: {str(e)}",
                calculation_type="market_demand_level",
                data_context={'cluster_size': len(cluster_jobs)}
            ) from e

    def _calculate_promotion_frequency_or_fail(self, cluster_jobs: pd.DataFrame) -> str:
        """
        Calculate promotion frequency based on management level distribution.
        
        Returns:
            str: 'high', 'medium', or 'low' based on promotion opportunity indicators
            
        Raises:
            DataQualityError: If cluster data is insufficient
            CalculationError: If calculation fails
        """
        if len(cluster_jobs) == 0:
            raise DataQualityError(
                "Cannot calculate promotion frequency for empty cluster",
                data_issue="empty_cluster",
                required_conditions="cluster must have at least 1 job"
            )
        
        try:
            management_levels = cluster_jobs.get('management_level', cluster_jobs.get('ManagementLevel', pd.Series()))
            
            if management_levels.empty:
                # No level data - estimate from cluster size
                cluster_size = len(cluster_jobs)
                return 'medium' if cluster_size >= 8 else 'low'
            
            # Factor 1: Management level spread (more levels = more promotion paths)
            unique_levels = len(management_levels.unique())
            level_spread_score = min(1.0, unique_levels / 5.0)
            
            # Factor 2: Cluster size (larger clusters = more opportunities)
            cluster_size = len(cluster_jobs)
            if cluster_size >= 20:
                size_score = 1.0
            elif cluster_size >= 10:
                size_score = 0.7
            elif cluster_size >= 5:
                size_score = 0.5
            else:
                size_score = 0.3
            
            # Factor 3: Check for junior/senior mix (good for promotions)
            level_text = ' '.join(management_levels.astype(str).str.lower())
            has_junior = any(term in level_text for term in ['junior', 'graduate', 'entry', 'analyst'])
            has_senior = any(term in level_text for term in ['senior', 'lead', 'manager', 'director'])
            
            progression_score = 0.8 if (has_junior and has_senior) else 0.4
            
            # Calculate weighted promotion frequency
            promotion_score = (level_spread_score * 0.4) + (size_score * 0.3) + (progression_score * 0.3)
            
            # Categorize frequency
            if promotion_score >= 0.7:
                return 'high'
            elif promotion_score >= 0.4:
                return 'medium'
            else:
                return 'low'
                
        except Exception as e:
            if isinstance(e, (DataQualityError, CalculationError)):
                raise
            
            raise CalculationError(
                f"Promotion frequency calculation failed: {str(e)}",
                calculation_type="promotion_frequency",
                data_context={'cluster_size': len(cluster_jobs)}
            ) from e

    def _calculate_lateral_movement_potential_or_fail(self, cluster_jobs: pd.DataFrame) -> str:
        """
        Calculate lateral movement potential based on job function diversity and cluster connectivity.
        
        Returns:
            str: 'high', 'medium', or 'low' based on lateral movement opportunities
            
        Raises:
            DataQualityError: If cluster data is insufficient
            CalculationError: If calculation fails
        """
        if len(cluster_jobs) == 0:
            raise DataQualityError(
                "Cannot calculate lateral movement potential for empty cluster",
                data_issue="empty_cluster",
                required_conditions="cluster must have at least 1 job"
            )
        
        try:
            # Factor 1: Job function diversity (more functions = more lateral options)
            job_functions = cluster_jobs.get('job_function', cluster_jobs.get('JobFunction', pd.Series()))
            if not job_functions.empty:
                function_diversity = len(job_functions.unique())
                # High diversity suggests good lateral movement
                if function_diversity >= 3:
                    diversity_score = 1.0
                elif function_diversity >= 2:
                    diversity_score = 0.7
                else:
                    diversity_score = 0.4
            else:
                diversity_score = 0.5  # Neutral
            
            # Factor 2: Cluster size (larger clusters = more lateral opportunities)
            cluster_size = len(cluster_jobs)
            if cluster_size >= 15:
                size_score = 1.0
            elif cluster_size >= 8:
                size_score = 0.8
            elif cluster_size >= 4:
                size_score = 0.6
            else:
                size_score = 0.4
            
            # Factor 3: Management level consistency (same levels = easier lateral moves)
            management_levels = cluster_jobs.get('management_level', cluster_jobs.get('ManagementLevel', pd.Series()))
            if not management_levels.empty:
                unique_levels = len(management_levels.unique())
                # Fewer levels (more consistency) = easier lateral movement
                if unique_levels <= 2:
                    level_score = 1.0
                elif unique_levels <= 4:
                    level_score = 0.7
                else:
                    level_score = 0.5
            else:
                level_score = 0.6  # Neutral
            
            # Calculate weighted lateral movement potential
            lateral_score = (diversity_score * 0.4) + (size_score * 0.3) + (level_score * 0.3)
            
            # Categorize potential
            if lateral_score >= 0.7:
                return 'high'
            elif lateral_score >= 0.5:
                return 'medium'
            else:
                return 'low'
                
        except Exception as e:
            if isinstance(e, (DataQualityError, CalculationError)):
                raise
            
            raise CalculationError(
                f"Lateral movement potential calculation failed: {str(e)}",
                calculation_type="lateral_movement_potential",
                data_context={'cluster_size': len(cluster_jobs)}
            ) from e

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
                    'business_value_score': self._calculate_business_value_score_or_fail(cluster_jobs, metrics),
                    'career_pathway_potential': self._calculate_career_pathway_potential_or_fail(cluster_jobs),
                    'skill_transferability': self._calculate_skill_transferability_or_fail(cluster_jobs),
                    'market_demand_level': self._calculate_market_demand_level_or_fail(cluster_jobs),
                    'typical_career_stage': self._calculate_typical_career_stage_or_fail(cluster_jobs),
                    'promotion_frequency': self._calculate_promotion_frequency_or_fail(cluster_jobs),
                    'lateral_movement_potential': self._calculate_lateral_movement_potential_or_fail(cluster_jobs),
                    'clustering_algorithm': char.get('clustering_algorithm', 'DBSCAN'),
                    'algorithm_parameters': char.get('algorithm_parameters', ''),
                    'quality_validation_date': datetime.now().isoformat(),
                    'business_review_date': datetime.now().isoformat(),
                    'created_timestamp': datetime.now().isoformat()
                })
        
        return pd.DataFrame(characteristics)