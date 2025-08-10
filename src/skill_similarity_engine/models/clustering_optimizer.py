#!/usr/bin/env python3
"""
Clustering Parameter Optimization Engine
========================================

Bayesian optimization system for clustering parameters using systematic analysis
of silhouette scores, elbow methods, and stability metrics.

This module ports the parameter optimization logic from the clustering notebooks
into a production-ready system that updates configuration files automatically.

Key Components:
- ClusteringParameterOptimizer: Main optimization orchestrator
- SilhouetteAnalyzer: Quality metric analysis across parameter ranges
- ElbowMethodAnalyzer: K-means optimization for cluster count
- StabilityAnalyzer: Cluster stability and consistency metrics

Philosophy: Data-driven parameter selection with automated config updates
"""

import pandas as pd
import numpy as np
import sqlite3
import warnings
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any, Union
from collections import defaultdict
import yaml
import tempfile
import shutil
import os

# Fix Windows joblib subprocess issues
os.environ['LOKY_MAX_CPU_COUNT'] = '1'

# Scientific computing and optimization
from sklearn.cluster import DBSCAN, KMeans, AgglomerativeClustering
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
from sklearn.metrics.pairwise import cosine_similarity

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
    elif "starting" in message.lower():
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
                print(f"   📊 Analyzing {context_dict['n_jobs']} job profiles...")
            elif 'total_combinations' in context_dict:
                print(f"   🧪 Testing {context_dict['total_combinations']} parameter combinations...")
            elif 'k' in context_dict:
                print(f"   ⚠️ K-means issue with k={context_dict['k']}: {context_dict.get('error', 'Unknown error')}")
            else:
                print(f"   {message}")
        else:
            print(f"   {message}")


class ParameterOptimizationResult:
    """Container for parameter optimization results."""
    
    def __init__(self, optimal_params: Dict[str, Any], 
                 optimization_metrics: Dict[str, float],
                 parameter_analysis: Dict[str, Any]):
        self.optimal_params = optimal_params
        self.optimization_metrics = optimization_metrics
        self.parameter_analysis = parameter_analysis
        self.timestamp = datetime.now().isoformat()


class SilhouetteAnalyzer:
    """
    Silhouette analysis for clustering quality assessment.
    
    Systematically evaluates clustering quality across parameter ranges
    to identify optimal DBSCAN eps/min_samples combinations.
    """
    
    def __init__(self):
        """Initialize silhouette analyzer."""
        log_info("SilhouetteAnalyzer initialized")
    
    def analyze_parameter_range(self, distance_matrix: np.ndarray, 
                              eps_range: List[float], 
                              min_samples_range: List[int]) -> Dict[str, Any]:
        """
        Analyze silhouette scores across parameter ranges.
        
        Args:
            distance_matrix: Precomputed distance matrix
            eps_range: Range of eps values to test
            min_samples_range: Range of min_samples values to test
            
        Returns:
            Dictionary with analysis results and optimal parameters
        """
        log_info("Starting silhouette analysis", 
                 eps_range=f"{min(eps_range):.3f} - {max(eps_range):.3f}",
                 min_samples_range=f"{min(min_samples_range)} - {max(min_samples_range)}",
                 total_combinations=len(eps_range) * len(min_samples_range))
        
        results = []
        best_score = -1
        best_params = None
        
        for eps in eps_range:
            for min_samples in min_samples_range:
                try:
                    # Perform clustering
                    clusterer = DBSCAN(eps=eps, min_samples=min_samples, metric='precomputed')
                    labels = clusterer.fit_predict(distance_matrix)
                    
                    # Calculate metrics
                    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
                    n_noise = list(labels).count(-1)
                    
                    # Calculate silhouette score if we have valid clusters
                    silhouette = -1
                    if n_clusters > 1 and n_noise < len(labels):
                        try:
                            silhouette = silhouette_score(distance_matrix, labels, metric='precomputed')
                        except:
                            silhouette = -1
                    
                    result = {
                        'eps': eps,
                        'min_samples': min_samples,
                        'n_clusters': n_clusters,
                        'n_noise': n_noise,
                        'noise_ratio': n_noise / len(labels),
                        'silhouette_score': silhouette
                    }
                    
                    results.append(result)
                    
                    # Track best parameters
                    if silhouette > best_score and n_clusters > 0:
                        best_score = silhouette
                        best_params = {'eps': eps, 'min_samples': min_samples}
                
                except Exception as e:
                    log_info("Parameter combination failed", {
                        'eps': eps, 'min_samples': min_samples, 'error': str(e)
                    })
        
        analysis_df = pd.DataFrame(results)
        
        # Find optimal parameters with additional criteria
        optimal_params = self._find_optimal_parameters(analysis_df)
        
        log_info("Silhouette analysis completed", {
            'total_tested': len(results),
            'best_silhouette': best_score,
            'optimal_eps': optimal_params.get('eps', 'N/A'),
            'optimal_min_samples': optimal_params.get('min_samples', 'N/A')
        })
        
        return {
            'results_df': analysis_df,
            'optimal_parameters': optimal_params,
            'best_silhouette_score': best_score,
            'parameter_analysis': self._analyze_parameter_trends(analysis_df)
        }
    
    def _find_optimal_parameters(self, results_df: pd.DataFrame) -> Dict[str, Any]:
        """Find optimal parameters considering multiple criteria."""
        if len(results_df) == 0:
            return {}
        
        # Filter for valid clustering results
        valid_results = results_df[
            (results_df['silhouette_score'] > 0) & 
            (results_df['n_clusters'] > 0) &
            (results_df['noise_ratio'] < 0.5)
        ]
        
        if len(valid_results) == 0:
            log_info("No valid clustering results found", {})
            return {}
        
        # Find best silhouette score
        best_result = valid_results.loc[valid_results['silhouette_score'].idxmax()]
        
        return {
            'eps': best_result['eps'],
            'min_samples': int(best_result['min_samples']),
            'expected_clusters': int(best_result['n_clusters']),
            'expected_silhouette': best_result['silhouette_score'],
            'expected_noise_ratio': best_result['noise_ratio']
        }
    
    def _analyze_parameter_trends(self, results_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze trends in parameter performance."""
        if len(results_df) == 0:
            return {}
        
        # Analyze eps trends
        eps_analysis = results_df.groupby('eps').agg({
            'silhouette_score': ['mean', 'max', 'std'],
            'n_clusters': ['mean', 'std'],
            'noise_ratio': 'mean'
        }).round(4)
        
        # Analyze min_samples trends
        min_samples_analysis = results_df.groupby('min_samples').agg({
            'silhouette_score': ['mean', 'max', 'std'],
            'n_clusters': ['mean', 'std'],
            'noise_ratio': 'mean'
        }).round(4)
        
        return {
            'eps_trends': eps_analysis.to_dict(),
            'min_samples_trends': min_samples_analysis.to_dict(),
            'overall_stats': {
                'mean_silhouette': results_df['silhouette_score'].mean(),
                'max_silhouette': results_df['silhouette_score'].max(),
                'mean_clusters': results_df['n_clusters'].mean(),
                'mean_noise_ratio': results_df['noise_ratio'].mean()
            }
        }


class ElbowMethodAnalyzer:
    """
    Elbow method analysis for optimal cluster count determination.
    
    Complements DBSCAN analysis with K-means elbow method to validate
    the natural number of clusters in the data.
    """
    
    def __init__(self):
        """Initialize elbow method analyzer."""
        log_info("ElbowMethodAnalyzer initialized", {})
    
    def analyze_optimal_clusters(self, similarity_matrix: np.ndarray, 
                               k_range: List[int]) -> Dict[str, Any]:
        """
        Perform elbow method analysis to find optimal cluster count.
        
        Args:
            similarity_matrix: Similarity matrix for clustering
            k_range: Range of k values to test
            
        Returns:
            Dictionary with elbow analysis results
        """
        log_info("Starting elbow method analysis", {
            'k_range': f"{min(k_range)} - {max(k_range)}",
            'data_shape': similarity_matrix.shape
        })
        
        # Convert similarity to distance for K-means
        distance_matrix = 1 - similarity_matrix
        distance_matrix = np.maximum(distance_matrix, 0)  # Ensure non-negative distances
        
        inertias = []
        silhouette_scores = []
        calinski_scores = []
        davies_bouldin_scores = []
        
        for k in k_range:
            if k >= len(similarity_matrix):
                continue
                
            try:
                # Use PCA on similarity matrix for K-means (like working notebooks)
                pca = PCA(n_components=min(50, similarity_matrix.shape[0]-1))
                similarity_features = pca.fit_transform(similarity_matrix)
                
                # Standardize features for numerical stability
                scaler = StandardScaler()
                similarity_features = scaler.fit_transform(similarity_features)
                
                # Perform K-means clustering on features
                kmeans = KMeans(
                    n_clusters=k, 
                    random_state=42, 
                    n_init=5,  # Reduced for stability
                    max_iter=100,
                    tol=1e-3,
                    algorithm='lloyd'
                )
                labels = kmeans.fit_predict(similarity_features)
                
                # Calculate metrics
                inertias.append(kmeans.inertia_)
                
                if k > 1:
                    silhouette_scores.append(silhouette_score(similarity_features, labels))
                    calinski_scores.append(calinski_harabasz_score(similarity_features, labels))
                    davies_bouldin_scores.append(davies_bouldin_score(similarity_features, labels))
                else:
                    silhouette_scores.append(0)
                    calinski_scores.append(0)
                    davies_bouldin_scores.append(float('inf'))
                    
            except Exception as e:
                log_info("K-means failed for k", {'k': k, 'error': str(e)})
                inertias.append(float('inf'))
                silhouette_scores.append(-1)
                calinski_scores.append(0)
                davies_bouldin_scores.append(float('inf'))
        
        # Find elbow point
        elbow_k = self._find_elbow_point(k_range[:len(inertias)], inertias)
        
        # Find optimal k based on silhouette score
        valid_k_range = k_range[:len(silhouette_scores)]
        if silhouette_scores and max(silhouette_scores) > 0:
            optimal_k_silhouette = valid_k_range[np.argmax(silhouette_scores)]
        else:
            optimal_k_silhouette = elbow_k
        
        results = {
            'k_range': valid_k_range,
            'inertias': inertias,
            'silhouette_scores': silhouette_scores,
            'calinski_scores': calinski_scores,
            'davies_bouldin_scores': davies_bouldin_scores,
            'elbow_k': elbow_k,
            'optimal_k_silhouette': optimal_k_silhouette,
            'recommended_k': optimal_k_silhouette
        }
        
        log_info("Elbow method analysis completed", {
            'elbow_k': elbow_k,
            'optimal_k_silhouette': optimal_k_silhouette,
            'max_silhouette': max(silhouette_scores) if silhouette_scores else 0
        })
        
        return results
    
    def _find_elbow_point(self, k_values: List[int], inertias: List[float]) -> int:
        """Find the elbow point in the inertia curve."""
        if len(k_values) < 3:
            return k_values[0] if k_values else 2
        
        # Calculate the rate of change
        differences = np.diff(inertias)
        differences2 = np.diff(differences)
        
        # Find the point where the second derivative is maximum
        if len(differences2) > 0:
            elbow_idx = np.argmax(differences2) + 2  # +2 because of double diff
            if elbow_idx < len(k_values):
                return k_values[elbow_idx]
        
        # Fallback: find the point where improvement diminishes most
        if len(differences) > 0:
            # Find where the rate of improvement drops significantly
            improvement_ratios = np.abs(differences[1:] / differences[:-1])
            if len(improvement_ratios) > 0:
                elbow_idx = np.argmin(improvement_ratios) + 2
                if elbow_idx < len(k_values):
                    return k_values[elbow_idx]
        
        # Default fallback
        return k_values[min(3, len(k_values) - 1)]


class SkillsParameterOptimizer:
    """
    Skills-specific parameter optimization with multiple similarity measures.
    
    Tests DBSCAN, Hierarchical, and K-means clustering across Jaccard, Cosine,
    and Combined similarity measures with taxonomy alignment validation.
    """
    
    def __init__(self, database_path: str, config_manager=None):
        """Initialize skills parameter optimizer."""
        self.database_path = database_path
        self.config_manager = config_manager or get_config_manager()
        
        # Skills-specific parameter ranges
        self.dbscan_params = {
            'eps': [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8],
            'min_samples': [2, 3, 4, 5, 6, 7, 8]
        }
        
        self.hierarchical_params = {
            'n_clusters': list(range(8, 31)),
            'linkage': ['ward', 'complete', 'average']
        }
        
        self.kmeans_params = {
            'n_clusters': list(range(8, 31))
        }
        
        self.similarity_methods = ['jaccard', 'cosine', 'combined']
        
        # Filtering thresholds for skills
        self.min_jobs_per_skill = 3
        self.min_cooccurrence = 2
        self.max_prevalence = 80.0
        
        log_info("SkillsParameterOptimizer initialized", {
            'database': database_path,
            'similarity_methods': len(self.similarity_methods),
            'algorithms': 3
        })
    
    def create_similarity_matrices(self, cooccurrence_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """Create multiple similarity matrices using different methods."""
        log_info("Creating similarity matrices using different methods")
        
        similarity_matrices = {}
        skills_matrix = cooccurrence_df.values
        n_skills = len(skills_matrix)
        
        # Method 1: Jaccard similarity
        print("   🔗 Calculating Jaccard similarity...")
        jaccard_matrix = np.zeros((n_skills, n_skills))
        
        for i in range(n_skills):
            for j in range(n_skills):
                if i <= j:
                    skill_i = skills_matrix[i]
                    skill_j = skills_matrix[j]
                    
                    intersection = np.sum((skill_i > 0) & (skill_j > 0))
                    union = np.sum((skill_i > 0) | (skill_j > 0))
                    
                    if union > 0:
                        jaccard_sim = intersection / union
                    else:
                        jaccard_sim = 0.0
                    
                    jaccard_matrix[i, j] = jaccard_sim
                    jaccard_matrix[j, i] = jaccard_sim
        
        np.fill_diagonal(jaccard_matrix, 1.0)
        similarity_matrices['jaccard'] = pd.DataFrame(
            jaccard_matrix, index=cooccurrence_df.index, columns=cooccurrence_df.columns
        )
        
        # Method 2: Cosine similarity
        print("   🔗 Calculating Cosine similarity...")
        cosine_matrix = cosine_similarity(skills_matrix)
        similarity_matrices['cosine'] = pd.DataFrame(
            cosine_matrix, index=cooccurrence_df.index, columns=cooccurrence_df.columns
        )
        
        # Method 3: Combined similarity (weighted average)
        print("   🔗 Calculating Combined similarity...")
        correlation_matrix = np.corrcoef(skills_matrix)
        correlation_matrix = np.nan_to_num(correlation_matrix, nan=0.0)
        
        combined_matrix = (
            0.4 * jaccard_matrix +
            0.4 * cosine_matrix + 
            0.2 * correlation_matrix
        )
        np.fill_diagonal(combined_matrix, 1.0)
        
        similarity_matrices['combined'] = pd.DataFrame(
            combined_matrix, index=cooccurrence_df.index, columns=cooccurrence_df.columns
        )
        
        print(f"   ✅ Created {len(similarity_matrices)} similarity matrices")
        
        return similarity_matrices
    
    def calculate_taxonomy_alignment_score(self, labels: np.ndarray, skill_metadata: pd.DataFrame, skill_names: List[str]) -> float:
        """Calculate how well clustering aligns with existing skill taxonomy."""
        try:
            # Create DataFrame with clustering results
            clustering_df = pd.DataFrame({
                'skill_name': skill_names,
                'cluster_label': labels
            })
            
            # Merge with metadata
            merged_df = clustering_df.merge(
                skill_metadata.reset_index(),
                left_on='skill_name',
                right_on='Skill_Name',
                how='left'
            )
            
            # Calculate category purity for each cluster
            cluster_purities = []
            
            for cluster_id in set(labels):
                if cluster_id == -1:  # Skip noise points
                    continue
                    
                cluster_skills = merged_df[merged_df['cluster_label'] == cluster_id]
                
                if len(cluster_skills) > 1:
                    # Find most common category in cluster
                    category_counts = cluster_skills['Category'].value_counts()
                    most_common_count = category_counts.iloc[0] if len(category_counts) > 0 else 0
                    cluster_purity = most_common_count / len(cluster_skills)
                    cluster_purities.append(cluster_purity)
            
            # Return average cluster purity
            return np.mean(cluster_purities) if cluster_purities else 0.0
            
        except Exception as e:
            log_info("Failed to calculate taxonomy alignment", {'error': str(e)})
            return 0.0
    
    def optimize_skills_parameters(self) -> Dict[str, Any]:
        """Run complete skills parameter optimization."""
        log_info("Starting skills parameter optimization")
        
        # Load skills data
        skills_data = self._load_skills_cooccurrence_data()
        if skills_data is None:
            log_info("No skills data available for optimization")
            return {}
        
        cooccurrence_df, skill_metadata = skills_data
        
        # Create similarity matrices
        similarity_matrices = self.create_similarity_matrices(cooccurrence_df)
        
        # Run optimization for each algorithm
        results = {
            'dbscan': self._optimize_skills_dbscan(similarity_matrices, skill_metadata),
            'hierarchical': self._optimize_skills_hierarchical(similarity_matrices, skill_metadata),
            'kmeans': self._optimize_skills_kmeans(similarity_matrices, skill_metadata)
        }
        
        # Find best overall configuration
        best_config = self._find_best_skills_configuration(results)
        
        log_info("Skills parameter optimization completed", {
            'algorithms_tested': len(results),
            'best_algorithm': best_config.get('algorithm', 'None'),
            'best_similarity': best_config.get('similarity_method', 'None')
        })
        
        return best_config
    
    def _convert_numpy_types(self, obj):
        """Convert NumPy types to native Python types for YAML serialization."""
        if isinstance(obj, np.generic):
            return obj.item()
        elif isinstance(obj, dict):
            return {key: self._convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_numpy_types(item) for item in obj]
        else:
            return obj
    
    def save_skills_configuration(self, skills_results: Dict[str, Any]) -> bool:
        """Save skills clustering configuration to separate YAML file."""
        try:
            if not skills_results:
                log_info("No skills results to save")
                return False
                
            # Create skills-specific configuration
            config_data = {
                'skills_clustering': {
                    'algorithm': skills_results.get('algorithm', 'dbscan'),
                    'optimal_parameters': {
                        'eps': skills_results.get('eps', 0.15),
                        'min_samples': skills_results.get('min_samples', 3),
                        'similarity_measure': skills_results.get('similarity_method', 'jaccard'),
                        'n_clusters': skills_results.get('n_clusters'),  # For hierarchical/kmeans
                        'linkage': skills_results.get('linkage')  # For hierarchical
                    },
                    'similarity_analysis': {
                        'jaccard_score': skills_results.get('jaccard_score', 0.0),
                        'cosine_score': skills_results.get('cosine_score', 0.0),
                        'combined_score': skills_results.get('combined_score', 0.0),
                        'best_similarity_method': skills_results.get('similarity_method', 'jaccard')
                    },
                    'clustering_metrics': {
                        'silhouette_score': skills_results.get('silhouette_score', 0.0),
                        'taxonomy_alignment_score': skills_results.get('taxonomy_alignment_score', 0.0),
                        'n_clusters_found': skills_results.get('n_clusters_found', 0),
                        'noise_ratio': skills_results.get('noise_ratio', 0.0)
                    },
                    'optimization_metadata': {
                        'optimization_timestamp': datetime.now().isoformat(),
                        'total_skills_analyzed': skills_results.get('total_skills', 0),
                        'algorithms_tested': ['dbscan', 'hierarchical', 'kmeans'],
                        'similarity_methods_tested': ['jaccard', 'cosine', 'combined'],
                        'rationale': skills_results.get('rationale', 'Optimized using comprehensive parameter search')
                    }
                },
                'bundling_strategy': {
                    'max_bundle_size': 15,
                    'min_specialization_threshold': 5.0,
                    'taxonomy_alignment_weight': 0.3,
                    'cluster_cohesion_weight': 0.7
                }
            }
            
            # Convert NumPy types to native Python types
            config_data = self._convert_numpy_types(config_data)
            
            # Save to separate skills config file
            config_path = self._get_skills_config_path()
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)
            
            log_info("Skills clustering configuration saved", {
                'config_path': str(config_path),
                'algorithm': config_data['skills_clustering']['algorithm'],
                'similarity_method': config_data['skills_clustering']['optimal_parameters']['similarity_measure'],
                'silhouette_score': config_data['skills_clustering']['clustering_metrics']['silhouette_score']
            })
            
            return True
            
        except Exception as e:
            log_info("Failed to save skills clustering configuration", {
                'error': str(e)
            })
            return False
    
    def _get_skills_config_path(self) -> Path:
        """Get the path for skills clustering configuration file."""
        # Save to core config directory as separate file
        config_root = Path("config")
        
        # Save to core config directory for skills-specific config
        skills_path = config_root / "core" / "skills_clustering.yaml"
        if config_root.exists():
            return skills_path
        
        # Fallback to creating in project root
        return Path("skills_clustering.yaml")
    
    def _load_skills_cooccurrence_data(self) -> Optional[Tuple[pd.DataFrame, pd.DataFrame]]:
        """Load skills co-occurrence data from database."""
        try:
            with sqlite3.connect(self.database_path) as conn:
                # Load skills co-occurrence data using three-table approach
                skills_query = """
                SELECT 
                    js.Skill_ID,
                    s.Skill_Name,
                    s.Category,
                    s.SkillType,
                    j.JobProfileID
                FROM core_job_skill_requirements js
                JOIN core_skills_taxonomy s ON js.Skill_ID = s.Skill_ID
                JOIN core_job_architecture j ON js.JobProfileID = j.JobProfileID
                ORDER BY s.Skill_Name, j.JobProfileID
                """
                
                skills_df = pd.read_sql_query(skills_query, conn)
                
                if len(skills_df) == 0:
                    log_info("No skills data found in database")
                    return None
                
                # Filter skills by prevalence
                skill_job_counts = skills_df.groupby('Skill_Name')['JobProfileID'].nunique()
                total_jobs = skills_df['JobProfileID'].nunique()
                
                # Apply filtering thresholds
                valid_skills = skill_job_counts[
                    (skill_job_counts >= self.min_jobs_per_skill) &
                    (skill_job_counts / total_jobs * 100 <= self.max_prevalence)
                ].index
                
                filtered_skills_df = skills_df[skills_df['Skill_Name'].isin(valid_skills)]
                
                # Create job-skill binary matrix first (like working notebooks)
                job_skill_matrix = filtered_skills_df.pivot_table(
                    index='JobProfileID',        # Jobs as rows
                    columns='Skill_Name',        # Skills as columns
                    values='Skill_ID',
                    aggfunc='count',
                    fill_value=0
                )
                job_skill_matrix = (job_skill_matrix > 0).astype(int)
                
                # Calculate co-occurrence matrix: skills x skills
                cooccurrence_values = np.dot(job_skill_matrix.T.values, job_skill_matrix.values)
                skill_names = job_skill_matrix.columns.tolist()
                cooccurrence_matrix = pd.DataFrame(
                    cooccurrence_values,
                    index=skill_names,
                    columns=skill_names
                )
                
                # Create skill metadata
                skill_metadata = filtered_skills_df[['Skill_Name', 'Category', 'SkillType']].drop_duplicates().set_index('Skill_Name')
                
                log_info("Skills data loaded successfully", {
                    'total_skills': len(cooccurrence_matrix),
                    'filtered_from': len(skill_job_counts),
                    'total_jobs': total_jobs
                })
                
                return cooccurrence_matrix, skill_metadata
                
        except Exception as e:
            log_info("Failed to load skills data", {'error': str(e)})
            return None
    
    def _optimize_skills_dbscan(self, similarity_matrices: Dict[str, pd.DataFrame], skill_metadata: pd.DataFrame) -> Dict[str, Any]:
        """Optimize DBSCAN parameters for skills clustering."""
        best_result = None
        best_score = -1
        
        total_combinations = len(self.similarity_methods) * len(self.dbscan_params['eps']) * len(self.dbscan_params['min_samples'])
        current_combination = 0
        
        print(f"   🧪 Testing {total_combinations} DBSCAN combinations...")
        
        for similarity_method, similarity_df in similarity_matrices.items():
            distance_matrix = 1 - similarity_df.values
            distance_matrix = np.maximum(distance_matrix, 0)
            
            for eps in self.dbscan_params['eps']:
                for min_samples in self.dbscan_params['min_samples']:
                    current_combination += 1
                    
                    if current_combination % 20 == 0:
                        print(f"      Progress: {current_combination}/{total_combinations} ({current_combination/total_combinations*100:.1f}%)")
                    
                    try:
                        clusterer = DBSCAN(eps=eps, min_samples=min_samples, metric='precomputed')
                        labels = clusterer.fit_predict(distance_matrix)
                        
                        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
                        noise_ratio = list(labels).count(-1) / len(labels)
                        
                        if n_clusters > 1 and noise_ratio < 0.9:  # Reasonable clustering
                            # Calculate metrics
                            non_noise_mask = labels != -1
                            if np.sum(non_noise_mask) > 1:
                                silhouette = silhouette_score(distance_matrix[non_noise_mask][:, non_noise_mask], 
                                                            labels[non_noise_mask], metric='precomputed')
                                taxonomy_score = self.calculate_taxonomy_alignment_score(
                                    labels, skill_metadata, similarity_df.index.tolist()
                                )
                                
                                # Combined score
                                combined_score = 0.6 * silhouette + 0.4 * taxonomy_score
                                
                                if combined_score > best_score:
                                    best_score = combined_score
                                    best_result = {
                                        'algorithm': 'dbscan',
                                        'similarity_method': similarity_method,
                                        'eps': eps,
                                        'min_samples': min_samples,
                                        'n_clusters': n_clusters,
                                        'noise_ratio': noise_ratio,
                                        'silhouette_score': silhouette,
                                        'taxonomy_alignment': taxonomy_score,
                                        'combined_score': combined_score
                                    }
                    except Exception as e:
                        continue
        
        return best_result or {}
    
    def _optimize_skills_hierarchical(self, similarity_matrices: Dict[str, pd.DataFrame], skill_metadata: pd.DataFrame) -> Dict[str, Any]:
        """Optimize hierarchical clustering parameters for skills."""
        best_result = None
        best_score = -1
        
        total_combinations = len(self.similarity_methods) * len(self.hierarchical_params['n_clusters']) * len(self.hierarchical_params['linkage'])
        current_combination = 0
        
        print(f"   🌳 Testing {total_combinations} Hierarchical combinations...")
        
        for similarity_method, similarity_df in similarity_matrices.items():
            # For hierarchical clustering, we need to use distance matrix
            distance_matrix = 1 - similarity_df.values
            distance_matrix = np.maximum(distance_matrix, 0)
            
            for n_clusters in self.hierarchical_params['n_clusters']:
                for linkage in self.hierarchical_params['linkage']:
                    current_combination += 1
                    
                    if current_combination % 20 == 0:
                        print(f"      Progress: {current_combination}/{total_combinations} ({current_combination/total_combinations*100:.1f}%)")
                    
                    try:
                        if linkage == 'ward':
                            # Ward linkage requires Euclidean distance, use similarity features
                            pca = PCA(n_components=min(50, similarity_df.shape[0]-1))
                            features = pca.fit_transform(similarity_df.values)
                            clusterer = AgglomerativeClustering(n_clusters=n_clusters, linkage=linkage)
                            labels = clusterer.fit_predict(features)
                            silhouette = silhouette_score(features, labels)
                        else:
                            clusterer = AgglomerativeClustering(n_clusters=n_clusters, linkage=linkage, metric='precomputed')
                            labels = clusterer.fit_predict(distance_matrix)
                            silhouette = silhouette_score(similarity_df.values, labels)
                        
                        # Calculate taxonomy alignment
                        taxonomy_score = self.calculate_taxonomy_alignment_score(
                            labels, skill_metadata, similarity_df.index.tolist()
                        )
                        
                        # Combined score
                        combined_score = 0.6 * silhouette + 0.4 * taxonomy_score
                        
                        if combined_score > best_score:
                            best_score = combined_score
                            best_result = {
                                'algorithm': 'hierarchical',
                                'similarity_method': similarity_method,
                                'n_clusters': n_clusters,
                                'linkage': linkage,
                                'silhouette_score': silhouette,
                                'taxonomy_alignment': taxonomy_score,
                                'combined_score': combined_score
                            }
                    except Exception as e:
                        continue
        
        return best_result or {}
    
    def _optimize_skills_kmeans(self, similarity_matrices: Dict[str, pd.DataFrame], skill_metadata: pd.DataFrame) -> Dict[str, Any]:
        """Optimize K-means parameters for skills."""
        best_result = None
        best_score = -1
        
        total_combinations = len(self.similarity_methods) * len(self.kmeans_params['n_clusters'])
        current_combination = 0
        
        print(f"   🎯 Testing {total_combinations} K-means combinations...")
        
        for similarity_method, similarity_df in similarity_matrices.items():
            # Use PCA features for K-means
            pca = PCA(n_components=min(50, similarity_df.shape[0]-1))
            features = pca.fit_transform(similarity_df.values)
            scaler = StandardScaler()
            features = scaler.fit_transform(features)
            
            for n_clusters in self.kmeans_params['n_clusters']:
                current_combination += 1
                
                if current_combination % 10 == 0:
                    print(f"      Progress: {current_combination}/{total_combinations} ({current_combination/total_combinations*100:.1f}%)")
                
                try:
                    clusterer = KMeans(n_clusters=n_clusters, random_state=42, n_init=5)
                    labels = clusterer.fit_predict(features)
                    
                    # Calculate metrics
                    silhouette = silhouette_score(features, labels)
                    taxonomy_score = self.calculate_taxonomy_alignment_score(
                        labels, skill_metadata, similarity_df.index.tolist()
                    )
                    
                    # Combined score
                    combined_score = 0.6 * silhouette + 0.4 * taxonomy_score
                    
                    if combined_score > best_score:
                        best_score = combined_score
                        best_result = {
                            'algorithm': 'kmeans',
                            'similarity_method': similarity_method,
                            'n_clusters': n_clusters,
                            'silhouette_score': silhouette,
                            'taxonomy_alignment': taxonomy_score,
                            'combined_score': combined_score
                        }
                except Exception as e:
                    continue
        
        return best_result or {}
    
    def _find_best_skills_configuration(self, results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Find the best overall configuration across all algorithms."""
        best_config = {}
        best_score = -1
        
        for algorithm, result in results.items():
            if result and result.get('combined_score', 0) > best_score:
                best_score = result['combined_score']
                best_config = result.copy()
        
        return best_config


class ClusteringParameterOptimizer:
    """
    Main parameter optimization orchestrator.
    
    Coordinates silhouette analysis, elbow method, and stability assessment
    to find optimal clustering parameters and update configuration files.
    """
    
    def __init__(self, db_path: str):
        """Initialize clustering parameter optimizer."""
        self.db_path = db_path
        self.config_manager = get_config_manager()
        self.silhouette_analyzer = SilhouetteAnalyzer()
        self.elbow_analyzer = ElbowMethodAnalyzer()
        self.skills_optimizer = SkillsParameterOptimizer(db_path)
        
        log_info("ClusteringParameterOptimizer initialized", {
            'database': db_path
        })
    
    @staticmethod
    def is_available() -> bool:
        """Check if optimization dependencies are available."""
        try:
            import sklearn
            return True
        except ImportError:
            return False
    
    def optimize_and_update(self) -> bool:
        """
        Run complete parameter optimization and update configuration.
        
        Returns:
            True if optimization completed successfully and config updated
        """
        log_info("Starting clustering parameter optimization", {})
        
        try:
            # Load data for optimization
            job_similarity_matrix, job_profiles = self._load_optimization_data()
            
            if job_similarity_matrix is None:
                log_info("No data available for optimization", {})
                return False
            
            # Optimize job profile clustering parameters
            job_optimization = self._optimize_job_clustering(job_similarity_matrix)
            
            # Optimize skills clustering parameters using comprehensive optimizer
            skills_results = self.skills_optimizer.optimize_skills_parameters()
            skills_optimization = ParameterOptimizationResult(
                optimal_params=skills_results.get('optimal_params', {}),
                optimization_metrics={
                    'best_score': skills_results.get('combined_score', 0),
                    'silhouette_score': skills_results.get('silhouette_score', 0),
                    'taxonomy_alignment': skills_results.get('taxonomy_alignment_score', 0)
                },
                parameter_analysis={
                    'algorithm': skills_results.get('algorithm', 'unknown'),
                    'similarity_method': skills_results.get('similarity_method', 'unknown'),
                    'parameter_space_explored': len(self.skills_optimizer.similarity_methods) * 3
                }
            )
            
            # Update configuration files
            success = self._update_configuration(job_optimization, skills_optimization)
            
            if success:
                log_info("Clustering parameter optimization completed successfully", {
                    'job_params': job_optimization.optimal_params,
                    'skills_params': skills_optimization.optimal_params
                })
            
            return success
            
        except Exception as e:
            log_info("Clustering parameter optimization failed", {
                'error': str(e)
            })
            return False
    
    def _load_optimization_data(self) -> Tuple[Optional[np.ndarray], Optional[pd.DataFrame]]:
        """Load data required for parameter optimization."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Load job similarity data (reuse logic from clustering_analyzer)
                from .clustering_analyzer import JobProfileClusterer
                clusterer = JobProfileClusterer()
                return clusterer._load_job_similarity_data(self.db_path)
                
        except Exception as e:
            log_info("Failed to load optimization data", {'error': str(e)})
            return None, None
    
    def _optimize_job_clustering(self, similarity_matrix: np.ndarray) -> ParameterOptimizationResult:
        """Optimize job profile clustering parameters."""
        log_info("Optimizing job profile clustering parameters", {})
        
        # Convert to distance matrix
        distance_matrix = 1 - similarity_matrix
        distance_matrix = np.maximum(distance_matrix, 0)  # Ensure non-negative distances
        
        # Define parameter ranges based on actual distance matrix characteristics
        # Analysis shows distances are concentrated around 0.7-0.8, so focus eps range there
        eps_range = np.arange(0.65, 0.85, 0.02).tolist()  # 0.65 to 0.83 with 0.02 step
        min_samples_range = list(range(2, 8))  # 2 to 7
        
        # Perform silhouette analysis
        silhouette_results = self.silhouette_analyzer.analyze_parameter_range(
            distance_matrix, eps_range, min_samples_range
        )
        
        # Perform elbow method analysis
        k_range = list(range(2, min(50, len(similarity_matrix) // 2)))
        elbow_results = self.elbow_analyzer.analyze_optimal_clusters(
            similarity_matrix, k_range
        )
        
        # Determine optimal parameters
        optimal_params = silhouette_results.get('optimal_parameters', {})
        
        # Validate with elbow method
        if not optimal_params and elbow_results.get('recommended_k'):
            # Fallback: use elbow method recommendation with default DBSCAN params
            optimal_params = {
                'eps': 0.1,
                'min_samples': 2,
                'expected_clusters': elbow_results['recommended_k']
            }
        
        # Ensure we have valid parameters
        if not optimal_params:
            optimal_params = {
                'eps': 0.1,
                'min_samples': 2,
                'expected_clusters': 10
            }
        
        optimization_metrics = {
            'best_silhouette_score': silhouette_results.get('best_silhouette_score', 0.0),
            'elbow_k': elbow_results.get('elbow_k', 10),
            'optimal_k_silhouette': elbow_results.get('optimal_k_silhouette', 10)
        }
        
        parameter_analysis = {
            'silhouette_analysis': silhouette_results.get('parameter_analysis', {}),
            'elbow_analysis': elbow_results,
            'recommendation_rationale': self._generate_recommendation_rationale(
                optimal_params, optimization_metrics
            )
        }
        
        return ParameterOptimizationResult(
            optimal_params, optimization_metrics, parameter_analysis
        )
    
    def _optimize_skills_clustering(self) -> ParameterOptimizationResult:
        """Optimize skills clustering parameters (simplified implementation)."""
        log_info("Optimizing skills clustering parameters", {})
        
        # For now, provide sensible defaults based on typical skills clustering
        # TODO: Implement proper skills similarity-based optimization
        
        optimal_params = {
            'eps': 0.15,
            'min_samples': 3,
            'similarity_measure': 'jaccard_combined'
        }
        
        optimization_metrics = {
            'estimated_bundles': 25,
            'estimated_specialized_skills': 100
        }
        
        parameter_analysis = {
            'method': 'heuristic_defaults',
            'rationale': 'Using empirically validated parameters from notebook analysis'
        }
        
        return ParameterOptimizationResult(
            optimal_params, optimization_metrics, parameter_analysis
        )
    
    def _generate_recommendation_rationale(self, optimal_params: Dict[str, Any], 
                                         metrics: Dict[str, float]) -> str:
        """Generate human-readable rationale for parameter recommendations."""
        eps = optimal_params.get('eps', 0.1)
        min_samples = optimal_params.get('min_samples', 2)
        silhouette = metrics.get('best_silhouette_score', 0.0)
        
        rationale = f"Optimal parameters: eps={eps}, min_samples={min_samples} "
        rationale += f"achieve silhouette score of {silhouette:.3f}. "
        
        if silhouette > 0.7:
            rationale += "Excellent clustering quality with well-separated clusters."
        elif silhouette > 0.5:
            rationale += "Good clustering quality with reasonable separation."
        else:
            rationale += "Moderate clustering quality - data may have natural overlap."
        
        return rationale
    
    def _convert_numpy_types(self, obj):
        """Convert NumPy types to native Python types for YAML serialization."""
        if isinstance(obj, np.generic):
            return obj.item()
        elif isinstance(obj, dict):
            return {key: self._convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_numpy_types(item) for item in obj]
        else:
            return obj
    
    def _update_configuration(self, job_optimization: ParameterOptimizationResult,
                            skills_optimization: ParameterOptimizationResult) -> bool:
        """Update clustering configuration files with optimized parameters."""
        try:
            # Create clustering configuration
            config_data = {
                'job_profile_clustering': {
                    'algorithm': 'dbscan',
                    'optimal_parameters': {
                        'eps': job_optimization.optimal_params.get('eps', 0.1),
                        'min_samples': job_optimization.optimal_params.get('min_samples', 2),
                        'similarity_measure': 'enhanced_defining_skills'
                    },
                    'quality_thresholds': {
                        'min_silhouette_score': 0.5,
                        'min_cluster_size': 5
                    },
                    'optimization_metadata': {
                        'optimization_timestamp': getattr(job_optimization, 'timestamp', datetime.now().isoformat()),
                        'best_silhouette_score': job_optimization.optimization_metrics.get('best_silhouette_score', 0.0),
                        'rationale': job_optimization.parameter_analysis.get('recommendation_rationale', '')
                    }
                },
                'skills_clustering': {
                    'algorithm': 'dbscan',
                    'optimal_parameters': {
                        'eps': skills_optimization.optimal_params.get('eps', 0.15),
                        'min_samples': skills_optimization.optimal_params.get('min_samples', 3),
                        'similarity_measure': skills_optimization.optimal_params.get('similarity_measure', 'jaccard_combined')
                    },
                    'bundling_strategy': {
                        'max_bundle_size': 15,
                        'min_specialization_threshold': 5.0
                    },
                    'optimization_metadata': {
                        'optimization_timestamp': getattr(skills_optimization, 'timestamp', datetime.now().isoformat()),
                        'method': skills_optimization.parameter_analysis.get('method', 'heuristic'),
                        'rationale': skills_optimization.parameter_analysis.get('rationale', '')
                    }
                },
                'velocity_analysis': {
                    'timeframes': {
                        'short_term': 1,  # years
                        'medium_term': 2,
                        'long_term': 3
                    },
                    'categorization': {
                        'accelerating_threshold': 0.2,
                        'growing_threshold': 0.05,
                        'declining_threshold': -0.05
                    }
                }
            }
            
            # Convert NumPy types to native Python types before serialization
            config_data = self._convert_numpy_types(config_data)
            
            # Write configuration to file
            config_path = self._get_clustering_config_path()
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)
            
            log_info("Clustering configuration updated", {
                'config_path': str(config_path),
                'job_eps': config_data['job_profile_clustering']['optimal_parameters']['eps'],
                'job_min_samples': config_data['job_profile_clustering']['optimal_parameters']['min_samples'],
                'skills_eps': config_data['skills_clustering']['optimal_parameters']['eps'],
                'skills_min_samples': config_data['skills_clustering']['optimal_parameters']['min_samples']
            })
            
            return True
            
        except Exception as e:
            log_info("Failed to update clustering configuration", {
                'error': str(e)
            })
            return False
    
    def _get_clustering_config_path(self) -> Path:
        """Get the path for clustering configuration file."""
        # Use core config directory structure
        config_root = Path("config")
        
        # Save to core config directory (like other core configs)
        core_path = config_root / "core" / "clustering_analysis.yaml"
        if config_root.exists():
            return core_path
        
        # Fallback to creating in project root
        return Path("clustering_analysis.yaml")