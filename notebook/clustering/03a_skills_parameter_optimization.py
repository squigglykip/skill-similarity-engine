#!/usr/bin/env python3
"""
SKILLS CLUSTERING - PARAMETER OPTIMIZATION
==========================================

Systematic parameter optimization for skills clustering to find optimal
clustering parameters before production runs. Tests multiple similarity measures,
clustering algorithms, and evaluates taxonomy alignment.

Purpose:
- Test DBSCAN, Hierarchical, and K-means parameters systematically
- Compare Jaccard, Cosine, and Combined similarity measures
- Evaluate clustering quality with silhouette analysis
- Assess taxonomy alignment and validation metrics
- Provide visual parameter selection guides
- Generate automated optimal parameter recommendations

Philosophy: Data-driven parameter selection with taxonomy validation focus

Usage:
    python 03a_skills_parameter_optimization.py
"""

import pandas as pd
import numpy as np
import sqlite3
import warnings
import os
from pathlib import Path
from datetime import datetime

# Fix Windows subprocess issues with scikit-learn
os.environ['LOKY_MAX_CPU_COUNT'] = '1'
from typing import Dict, List, Tuple, Optional, Set, Any
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import DBSCAN, KMeans, AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score, adjusted_rand_score
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from collections import defaultdict, Counter

warnings.filterwarnings('ignore')

# Set plotting style
try:
    plt.style.use('seaborn-v0_8')
except OSError:
    try:
        plt.style.use('seaborn')
    except OSError:
        plt.style.use('default')
sns.set_palette("husl")

# =============================================================================
# CONFIGURATION
# =============================================================================

DATABASE_FILE = "models/2025-Q3/workforce_intelligence.sqlite"

class SkillsParameterOptimizationConfig:
    """Configuration for skills clustering parameter optimization"""
    
    DATABASE_PATH = DATABASE_FILE
    
    # Filtering thresholds
    MIN_JOBS_PER_SKILL = 3        # Skills must appear in at least 3 jobs
    MIN_COOCCURRENCE = 2          # Skill pairs must co-occur at least 2 times
    MAX_PREVALENCE = 80.0         # Exclude skills in >80% of jobs (too universal)
    
    # DBSCAN parameter ranges to test
    DBSCAN_PARAMETER_GRID = {
        'eps': [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8],
        'min_samples': [2, 3, 4, 5, 6, 7, 8]
    }
    
    # Hierarchical clustering parameters
    HIERARCHICAL_PARAMETER_GRID = {
        'n_clusters': list(range(8, 31)),  # Test 8 to 30 clusters
        'linkage': ['ward', 'complete', 'average']
    }
    
    # K-means parameter ranges
    KMEANS_PARAMETER_GRID = {
        'n_clusters': list(range(8, 31))  # Test 8 to 30 clusters
    }
    
    # Similarity methods to test
    SIMILARITY_METHODS = ['jaccard', 'cosine', 'combined']
    
    # Evaluation settings
    EVALUATION_METRICS = [
        'silhouette_score',
        'calinski_harabasz_score', 
        'davies_bouldin_score',
        'taxonomy_alignment_score',
        'n_clusters',
        'noise_ratio'
    ]
    
    # Visualization settings
    SAVE_PLOTS = True
    PLOT_DPI = 300
    FIGURE_SIZE = (12, 8)

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def connect_database():
    """Connect to the workforce intelligence database"""
    try:
        conn = sqlite3.connect(SkillsParameterOptimizationConfig.DATABASE_PATH)
        print(f"✅ Connected to database: {SkillsParameterOptimizationConfig.DATABASE_PATH}")
        return conn
    except sqlite3.OperationalError as e:
        raise FileNotFoundError(f"Could not connect to database: {e}")

def save_plot(fig, filename: str, title: Optional[str] = None):
    """Save plot with timestamp"""
    if title:
        fig.suptitle(title, fontsize=14, fontweight='bold')
    
    if SkillsParameterOptimizationConfig.SAVE_PLOTS:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        full_filename = f"skills_param_opt_{filename}_{timestamp}.png"
        fig.savefig(full_filename, dpi=SkillsParameterOptimizationConfig.PLOT_DPI, bbox_inches='tight')
        print(f"   📊 Plot saved: {full_filename}")

# =============================================================================
# DATA LOADING AND PREPROCESSING
# =============================================================================

def load_skills_cooccurrence_data(conn) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load and preprocess skills co-occurrence data for clustering optimization"""
    print("📚 Loading skills co-occurrence data for parameter optimization...")
    
    job_skills_query = """
    SELECT 
        js.JobProfileID,
        js.Skill_ID,
        s.Skill_Name,
        s.Category as Skill_Category,
        s.SkillType,
        j.JobFunction,
        j.JobSubFunction
    FROM job_skills js
    JOIN skills s ON js.Skill_ID = s.Skill_ID
    JOIN jobs j ON js.JobProfileID = j.JobProfileID
    ORDER BY js.JobProfileID, s.Skill_Name
    """
    
    job_skills_df = pd.read_sql_query(job_skills_query, conn)
    
    # Calculate skill prevalence and filter
    total_jobs = job_skills_df['JobProfileID'].nunique()
    skill_stats = job_skills_df.groupby('Skill_Name').agg({
        'JobProfileID': 'nunique',
        'Skill_Category': 'first',
        'SkillType': 'first'
    }).reset_index()
    
    skill_stats['prevalence_percentage'] = (skill_stats['JobProfileID'] / total_jobs) * 100
    skill_stats = skill_stats.rename(columns={'JobProfileID': 'job_count'})
    
    # Apply filtering criteria
    filtered_skills = skill_stats[
        (skill_stats['job_count'] >= SkillsParameterOptimizationConfig.MIN_JOBS_PER_SKILL) &
        (skill_stats['prevalence_percentage'] <= SkillsParameterOptimizationConfig.MAX_PREVALENCE)
    ]['Skill_Name'].tolist()
    
    # Filter job-skills data
    filtered_job_skills = job_skills_df[
        job_skills_df['Skill_Name'].isin(filtered_skills)
    ].copy()
    
    print(f"   → Total skills: {job_skills_df['Skill_Name'].nunique():,}")
    print(f"   → Filtered skills: {len(filtered_skills):,}")
    print(f"   → Job-skill relationships: {len(filtered_job_skills):,}")
    
    # Create skill co-occurrence matrix
    print("   → Building skill co-occurrence matrix...")
    
    job_skill_matrix = filtered_job_skills.pivot_table(
        index='JobProfileID',
        columns='Skill_Name', 
        values='Skill_ID',
        aggfunc='count',
        fill_value=0
    )
    job_skill_matrix = (job_skill_matrix > 0).astype(int)
    
    cooccurrence_matrix = np.dot(job_skill_matrix.T.values, job_skill_matrix.values)
    
    skill_names = job_skill_matrix.columns.tolist()
    cooccurrence_df = pd.DataFrame(
        cooccurrence_matrix,
        index=skill_names,
        columns=skill_names
    )
    
    # Create skill metadata
    skill_metadata = skill_stats[skill_stats['Skill_Name'].isin(filtered_skills)].copy()
    skill_metadata = skill_metadata.set_index('Skill_Name')
    
    print(f"   → Co-occurrence matrix shape: {cooccurrence_df.shape}")
    
    return filtered_job_skills, cooccurrence_df, skill_metadata

def create_similarity_matrices(cooccurrence_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Create multiple similarity matrices using different methods
    
    Returns:
        Dict with similarity matrices for each method
    """
    print("🔗 Creating similarity matrices using different methods...")
    
    similarity_matrices = {}
    skills_matrix = cooccurrence_df.values
    n_skills = len(skills_matrix)
    
    # Method 1: Jaccard similarity
    print("   → Calculating Jaccard similarity...")
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
    print("   → Calculating Cosine similarity...")
    cosine_matrix = cosine_similarity(skills_matrix)
    similarity_matrices['cosine'] = pd.DataFrame(
        cosine_matrix, index=cooccurrence_df.index, columns=cooccurrence_df.columns
    )
    
    # Method 3: Combined similarity (weighted average)
    print("   → Calculating Combined similarity...")
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
    
    print(f"   → Created {len(similarity_matrices)} similarity matrices")
    
    return similarity_matrices

# =============================================================================
# PARAMETER OPTIMIZATION FUNCTIONS
# =============================================================================

def optimize_dbscan_parameters(
    similarity_matrices: Dict[str, pd.DataFrame],
    skill_metadata: pd.DataFrame
) -> pd.DataFrame:
    """
    Systematically test DBSCAN parameters across different similarity methods
    
    Returns:
        DataFrame with parameter combinations and evaluation metrics
    """
    print("\n🔍 OPTIMIZING DBSCAN PARAMETERS")
    print("="*50)
    
    results = []
    total_combinations = (
        len(SkillsParameterOptimizationConfig.DBSCAN_PARAMETER_GRID['eps']) *
        len(SkillsParameterOptimizationConfig.DBSCAN_PARAMETER_GRID['min_samples']) *
        len(SkillsParameterOptimizationConfig.SIMILARITY_METHODS)
    )
    
    print(f"   → Testing {total_combinations} parameter combinations...")
    
    combination_count = 0
    
    for similarity_method in SkillsParameterOptimizationConfig.SIMILARITY_METHODS:
        similarity_df = similarity_matrices[similarity_method]
        distance_matrix = 1 - similarity_df.values
        distance_matrix = np.maximum(distance_matrix, 0)
        
        for eps in SkillsParameterOptimizationConfig.DBSCAN_PARAMETER_GRID['eps']:
            for min_samples in SkillsParameterOptimizationConfig.DBSCAN_PARAMETER_GRID['min_samples']:
                combination_count += 1
                
                if combination_count % 50 == 0:
                    print(f"   → Progress: {combination_count}/{total_combinations} ({combination_count/total_combinations*100:.1f}%)")
                
                # Perform clustering
                dbscan = DBSCAN(eps=eps, min_samples=min_samples, metric='precomputed')
                labels = dbscan.fit_predict(distance_matrix)
                
                # Calculate basic metrics
                n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
                noise_points = list(labels).count(-1)
                noise_ratio = noise_points / len(labels)
                
                # Initialize quality metrics
                silhouette = None
                calinski_harabasz = None
                davies_bouldin = None
                taxonomy_alignment = None
                
                # Calculate quality metrics if we have valid clusters
                if n_clusters > 1 and noise_points < len(labels):
                    try:
                        non_noise_mask = labels != -1
                        if np.sum(non_noise_mask) > 1 and len(set(labels[non_noise_mask])) > 1:
                            non_noise_distance = distance_matrix[non_noise_mask][:, non_noise_mask]
                            non_noise_labels = labels[non_noise_mask]
                            
                            silhouette = silhouette_score(non_noise_distance, non_noise_labels, metric='precomputed')
                            
                            # For other metrics, use similarity matrix
                            non_noise_similarity = similarity_df.values[non_noise_mask][:, non_noise_mask]
                            calinski_harabasz = calinski_harabasz_score(non_noise_similarity, non_noise_labels)
                            davies_bouldin = davies_bouldin_score(non_noise_similarity, non_noise_labels)
                            
                            # Calculate taxonomy alignment
                            taxonomy_alignment = calculate_taxonomy_alignment_score(
                                labels, skill_metadata, similarity_df.index.tolist()
                            )
                            
                    except Exception as e:
                        pass
                
                results.append({
                    'similarity_method': similarity_method,
                    'eps': eps,
                    'min_samples': min_samples,
                    'n_clusters': n_clusters,
                    'noise_points': noise_points,
                    'noise_ratio': noise_ratio,
                    'silhouette_score': silhouette,
                    'calinski_harabasz_score': calinski_harabasz,
                    'davies_bouldin_score': davies_bouldin,
                    'taxonomy_alignment_score': taxonomy_alignment
                })
    
    results_df = pd.DataFrame(results)
    
    print(f"   → Completed DBSCAN parameter optimization")
    print(f"   → Valid clustering results: {results_df['silhouette_score'].notna().sum()}/{len(results_df)}")
    
    return results_df

def optimize_hierarchical_parameters(
    similarity_matrices: Dict[str, pd.DataFrame],
    skill_metadata: pd.DataFrame
) -> pd.DataFrame:
    """
    Test hierarchical clustering parameters across different similarity methods
    
    Returns:
        DataFrame with hierarchical clustering evaluation results
    """
    print("\n🔍 OPTIMIZING HIERARCHICAL CLUSTERING PARAMETERS")
    print("="*50)
    
    results = []
    total_combinations = (
        len(SkillsParameterOptimizationConfig.HIERARCHICAL_PARAMETER_GRID['n_clusters']) *
        len(SkillsParameterOptimizationConfig.HIERARCHICAL_PARAMETER_GRID['linkage']) *
        len(SkillsParameterOptimizationConfig.SIMILARITY_METHODS)
    )
    
    print(f"   → Testing {total_combinations} parameter combinations...")
    
    combination_count = 0
    
    for similarity_method in SkillsParameterOptimizationConfig.SIMILARITY_METHODS:
        similarity_df = similarity_matrices[similarity_method]
        distance_matrix = 1 - similarity_df.values
        distance_matrix = np.maximum(distance_matrix, 0)
        
        for n_clusters in SkillsParameterOptimizationConfig.HIERARCHICAL_PARAMETER_GRID['n_clusters']:
            for linkage in SkillsParameterOptimizationConfig.HIERARCHICAL_PARAMETER_GRID['linkage']:
                combination_count += 1
                
                if combination_count % 25 == 0:
                    print(f"   → Progress: {combination_count}/{total_combinations} ({combination_count/total_combinations*100:.1f}%)")
                
                try:
                    # Perform clustering
                    hierarchical = AgglomerativeClustering(
                        n_clusters=n_clusters,
                        linkage=linkage,
                        metric='precomputed' if linkage != 'ward' else 'euclidean'
                    )
                    
                    if linkage == 'ward':
                        # Ward requires euclidean distance, use similarity matrix directly
                        labels = hierarchical.fit_predict(similarity_df.values)
                        eval_matrix = similarity_df.values
                    else:
                        labels = hierarchical.fit_predict(distance_matrix)
                        eval_matrix = distance_matrix
                        eval_metric = 'precomputed'
                    
                    # Calculate quality metrics
                    if linkage == 'ward':
                        silhouette = silhouette_score(similarity_df.values, labels)
                        calinski_harabasz = calinski_harabasz_score(similarity_df.values, labels)
                        davies_bouldin = davies_bouldin_score(similarity_df.values, labels)
                    else:
                        silhouette = silhouette_score(distance_matrix, labels, metric='precomputed')
                        calinski_harabasz = calinski_harabasz_score(similarity_df.values, labels)
                        davies_bouldin = davies_bouldin_score(similarity_df.values, labels)
                    
                    # Calculate taxonomy alignment
                    taxonomy_alignment = calculate_taxonomy_alignment_score(
                        labels, skill_metadata, similarity_df.index.tolist()
                    )
                    
                    results.append({
                        'similarity_method': similarity_method,
                        'n_clusters': n_clusters,
                        'linkage': linkage,
                        'silhouette_score': silhouette,
                        'calinski_harabasz_score': calinski_harabasz,
                        'davies_bouldin_score': davies_bouldin,
                        'taxonomy_alignment_score': taxonomy_alignment
                    })
                    
                except Exception as e:
                    # Skip problematic combinations
                    continue
    
    results_df = pd.DataFrame(results)
    
    print(f"   → Completed hierarchical clustering optimization")
    print(f"   → Valid results: {len(results_df)}")
    
    return results_df

def optimize_kmeans_parameters(
    similarity_matrices: Dict[str, pd.DataFrame],
    skill_metadata: pd.DataFrame
) -> pd.DataFrame:
    """
    Apply elbow method and silhouette analysis for K-means optimization
    
    Returns:
        DataFrame with K-means evaluation results
    """
    print("\n🔍 OPTIMIZING K-MEANS PARAMETERS (ELBOW METHOD)")
    print("="*50)
    
    results = []
    
    for similarity_method in SkillsParameterOptimizationConfig.SIMILARITY_METHODS:
        similarity_df = similarity_matrices[similarity_method]
        
        # Use PCA to reduce dimensionality for K-means
        pca = PCA(n_components=min(50, similarity_df.shape[0]-1))
        similarity_features = pca.fit_transform(similarity_df.values)
        
        print(f"   → {similarity_method}: Reduced to {similarity_features.shape[1]} components")
        
        for n_clusters in SkillsParameterOptimizationConfig.KMEANS_PARAMETER_GRID['n_clusters']:
            try:
                # Perform K-means clustering
                kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
                labels = kmeans.fit_predict(similarity_features)
                
                # Calculate metrics
                inertia = kmeans.inertia_
                silhouette = silhouette_score(similarity_features, labels)
                calinski_harabasz = calinski_harabasz_score(similarity_features, labels)
                davies_bouldin = davies_bouldin_score(similarity_features, labels)
                
                # Calculate taxonomy alignment
                taxonomy_alignment = calculate_taxonomy_alignment_score(
                    labels, skill_metadata, similarity_df.index.tolist()
                )
                
                results.append({
                    'similarity_method': similarity_method,
                    'n_clusters': n_clusters,
                    'inertia': inertia,
                    'silhouette_score': silhouette,
                    'calinski_harabasz_score': calinski_harabasz,
                    'davies_bouldin_score': davies_bouldin,
                    'taxonomy_alignment_score': taxonomy_alignment
                })
                
            except Exception as e:
                continue
    
    results_df = pd.DataFrame(results)
    
    print(f"   → Completed K-means optimization")
    print(f"   → Valid results: {len(results_df)}")
    
    return results_df

def calculate_taxonomy_alignment_score(
    labels: np.ndarray,
    skill_metadata: pd.DataFrame,
    skill_names: List[str]
) -> float:
    """
    Calculate how well clustering aligns with existing skill taxonomy
    
    Returns:
        Alignment score (higher is better)
    """
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
                category_counts = cluster_skills['Skill_Category'].value_counts()
                most_common_count = category_counts.iloc[0] if len(category_counts) > 0 else 0
                cluster_purity = most_common_count / len(cluster_skills)
                cluster_purities.append(cluster_purity)
        
        # Return average cluster purity
        return np.mean(cluster_purities) if cluster_purities else 0.0
        
    except Exception as e:
        return 0.0

def find_optimal_parameters(
    dbscan_results: pd.DataFrame,
    hierarchical_results: pd.DataFrame,
    kmeans_results: pd.DataFrame
) -> Dict[str, Any]:
    """
    Analyze all results and recommend optimal parameters for each method
    
    Returns:
        Dict with optimal parameter recommendations
    """
    print("\n🏆 FINDING OPTIMAL PARAMETERS")
    print("="*50)
    
    recommendations = {}
    
    # DBSCAN optimization
    valid_dbscan = dbscan_results[dbscan_results['silhouette_score'].notna()].copy()
    
    if len(valid_dbscan) > 0:
        # Score DBSCAN results
        valid_dbscan['cluster_score'] = np.where(
            (valid_dbscan['n_clusters'] >= 8) & (valid_dbscan['n_clusters'] <= 25),
            1.0, 0.8
        )
        
        valid_dbscan['noise_score'] = np.where(
            valid_dbscan['noise_ratio'] <= 0.4, 1.0, 1.0 - valid_dbscan['noise_ratio']
        )
        
        valid_dbscan['composite_score'] = (
            0.4 * valid_dbscan['silhouette_score'] +
            0.2 * valid_dbscan['cluster_score'] +
            0.2 * valid_dbscan['noise_score'] +
            0.2 * valid_dbscan['taxonomy_alignment_score'].fillna(0)
        )
        
        best_dbscan = valid_dbscan.loc[valid_dbscan['composite_score'].idxmax()]
        
        recommendations['dbscan'] = {
            'similarity_method': best_dbscan['similarity_method'],
            'eps': best_dbscan['eps'],
            'min_samples': best_dbscan['min_samples'],
            'expected_clusters': best_dbscan['n_clusters'],
            'expected_noise_ratio': best_dbscan['noise_ratio'],
            'silhouette_score': best_dbscan['silhouette_score'],
            'taxonomy_alignment': best_dbscan['taxonomy_alignment_score'],
            'composite_score': best_dbscan['composite_score']
        }
        
        print(f"🥇 OPTIMAL DBSCAN PARAMETERS:")
        print(f"   → Similarity method: {best_dbscan['similarity_method']}")
        print(f"   → eps: {best_dbscan['eps']}")
        print(f"   → min_samples: {best_dbscan['min_samples']}")
        print(f"   → Expected clusters: {best_dbscan['n_clusters']}")
        print(f"   → Expected noise ratio: {best_dbscan['noise_ratio']:.1%}")
        print(f"   → Silhouette score: {best_dbscan['silhouette_score']:.3f}")
        print(f"   → Taxonomy alignment: {best_dbscan['taxonomy_alignment_score']:.3f}")
        
    else:
        recommendations['dbscan'] = None
    
    # Hierarchical optimization
    if len(hierarchical_results) > 0:
        hierarchical_results['composite_score'] = (
            0.4 * hierarchical_results['silhouette_score'] +
            0.3 * hierarchical_results['taxonomy_alignment_score'].fillna(0) +
            0.3 * (1 - hierarchical_results['davies_bouldin_score'])  # Lower is better for DB
        )
        
        best_hierarchical = hierarchical_results.loc[hierarchical_results['composite_score'].idxmax()]
        
        recommendations['hierarchical'] = {
            'similarity_method': best_hierarchical['similarity_method'],
            'n_clusters': best_hierarchical['n_clusters'],
            'linkage': best_hierarchical['linkage'],
            'silhouette_score': best_hierarchical['silhouette_score'],
            'taxonomy_alignment': best_hierarchical['taxonomy_alignment_score'],
            'davies_bouldin_score': best_hierarchical['davies_bouldin_score'],
            'composite_score': best_hierarchical['composite_score']
        }
        
        print(f"\n🥇 OPTIMAL HIERARCHICAL PARAMETERS:")
        print(f"   → Similarity method: {best_hierarchical['similarity_method']}")
        print(f"   → n_clusters: {best_hierarchical['n_clusters']}")
        print(f"   → linkage: {best_hierarchical['linkage']}")
        print(f"   → Silhouette score: {best_hierarchical['silhouette_score']:.3f}")
        print(f"   → Taxonomy alignment: {best_hierarchical['taxonomy_alignment_score']:.3f}")
        
    else:
        recommendations['hierarchical'] = None
    
    # K-means optimization
    if len(kmeans_results) > 0:
        # Group by similarity method and find elbow for each
        for method in kmeans_results['similarity_method'].unique():
            method_results = kmeans_results[kmeans_results['similarity_method'] == method].copy()
            method_results = method_results.sort_values('n_clusters')
            
            # Find elbow point
            inertia_diff = np.diff(method_results['inertia'].values)
            inertia_diff_2 = np.diff(inertia_diff)
            
            if len(inertia_diff_2) > 0:
                elbow_idx = np.argmax(inertia_diff_2) + 2
                elbow_clusters = method_results.iloc[elbow_idx]['n_clusters']
            else:
                elbow_clusters = None
            
            # Find best silhouette
            best_silhouette_idx = method_results['silhouette_score'].idxmax()
            best_silhouette = method_results.loc[best_silhouette_idx]
        
        # Overall best K-means
        kmeans_results['composite_score'] = (
            0.4 * kmeans_results['silhouette_score'] +
            0.3 * kmeans_results['taxonomy_alignment_score'].fillna(0) +
            0.3 * kmeans_results['calinski_harabasz_score'] / kmeans_results['calinski_harabasz_score'].max()
        )
        
        best_kmeans = kmeans_results.loc[kmeans_results['composite_score'].idxmax()]
        
        recommendations['kmeans'] = {
            'similarity_method': best_kmeans['similarity_method'],
            'n_clusters': best_kmeans['n_clusters'],
            'silhouette_score': best_kmeans['silhouette_score'],
            'taxonomy_alignment': best_kmeans['taxonomy_alignment_score'],
            'composite_score': best_kmeans['composite_score']
        }
        
        print(f"\n🥇 OPTIMAL K-MEANS PARAMETERS:")
        print(f"   → Similarity method: {best_kmeans['similarity_method']}")
        print(f"   → n_clusters: {best_kmeans['n_clusters']}")
        print(f"   → Silhouette score: {best_kmeans['silhouette_score']:.3f}")
        print(f"   → Taxonomy alignment: {best_kmeans['taxonomy_alignment_score']:.3f}")
        
    else:
        recommendations['kmeans'] = None
    
    return recommendations

# =============================================================================
# VISUALIZATION FUNCTIONS
# =============================================================================

def create_skills_parameter_optimization_visualizations(
    dbscan_results: pd.DataFrame,
    hierarchical_results: pd.DataFrame,
    kmeans_results: pd.DataFrame,
    recommendations: Dict[str, Any]
) -> None:
    """Create comprehensive skills parameter optimization visualizations"""
    print("\n📈 Creating skills parameter optimization visualizations...")
    
    # Create large figure with multiple subplots
    fig = plt.figure(figsize=(24, 20))
    
    # 1. DBSCAN parameter heatmaps by similarity method
    similarity_methods = dbscan_results['similarity_method'].unique()
    
    for i, method in enumerate(similarity_methods):
        method_data = dbscan_results[
            (dbscan_results['similarity_method'] == method) & 
            (dbscan_results['silhouette_score'].notna())
        ]
        
        if len(method_data) > 0:
            ax = plt.subplot(4, 3, i + 1)
            pivot_data = method_data.pivot(index='min_samples', columns='eps', values='silhouette_score')
            sns.heatmap(pivot_data, annot=True, fmt='.2f', cmap='viridis', ax=ax)
            ax.set_title(f'DBSCAN Silhouette Score - {method.title()}')
            ax.set_xlabel('eps')
            ax.set_ylabel('min_samples')
    
    # 4. Hierarchical clustering comparison
    if len(hierarchical_results) > 0:
        ax4 = plt.subplot(4, 3, 4)
        
        # Group by similarity method and linkage
        hierarchical_pivot = hierarchical_results.groupby(['similarity_method', 'linkage'])['silhouette_score'].max().reset_index()
        hierarchical_pivot_table = hierarchical_pivot.pivot(index='linkage', columns='similarity_method', values='silhouette_score')
        
        sns.heatmap(hierarchical_pivot_table, annot=True, fmt='.3f', cmap='plasma', ax=ax4)
        ax4.set_title('Best Hierarchical Silhouette Scores')
        ax4.set_xlabel('Similarity Method')
        ax4.set_ylabel('Linkage')
    
    # 5. K-means elbow curves by similarity method
    kmeans_methods = kmeans_results['similarity_method'].unique()
    
    for i, method in enumerate(kmeans_methods):
        method_data = kmeans_results[kmeans_results['similarity_method'] == method].sort_values('n_clusters')
        
        if len(method_data) > 0:
            ax = plt.subplot(4, 3, 5 + i)
            ax.plot(method_data['n_clusters'], method_data['inertia'], 'bo-', linewidth=2, markersize=6)
            ax.set_xlabel('Number of Clusters')
            ax.set_ylabel('Inertia')
            ax.set_title(f'K-means Elbow Curve - {method.title()}')
            ax.grid(True, alpha=0.3)
    
    # 8. Taxonomy alignment comparison
    ax8 = plt.subplot(4, 3, 8)
    
    # Collect taxonomy alignment scores
    taxonomy_scores = []
    method_labels = []
    
    for method_type in ['dbscan', 'hierarchical', 'kmeans']:
        if recommendations.get(method_type):
            taxonomy_scores.append(recommendations[method_type]['taxonomy_alignment'])
            method_labels.append(f"{method_type.title()}\n({recommendations[method_type]['similarity_method']})")
    
    if taxonomy_scores:
        bars = ax8.bar(method_labels, taxonomy_scores, color=['skyblue', 'lightcoral', 'lightgreen'][:len(taxonomy_scores)])
        ax8.set_ylabel('Taxonomy Alignment Score')
        ax8.set_title('Taxonomy Alignment by Method')
        ax8.grid(True, alpha=0.3, axis='y')
        
        # Add value labels
        for bar, score in zip(bars, taxonomy_scores):
            ax8.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{score:.3f}', ha='center', va='bottom', fontweight='bold')
    
    # 9. Overall method comparison
    ax9 = plt.subplot(4, 3, 9)
    
    # Collect overall scores
    overall_scores = []
    overall_labels = []
    
    for method_type in ['dbscan', 'hierarchical', 'kmeans']:
        if recommendations.get(method_type):
            if method_type == 'dbscan':
                score = recommendations[method_type]['composite_score']
            else:
                score = recommendations[method_type]['composite_score']
            overall_scores.append(score)
            overall_labels.append(f"{method_type.title()}\n({recommendations[method_type]['similarity_method']})")
    
    if overall_scores:
        bars = ax9.bar(overall_labels, overall_scores, color=['skyblue', 'lightcoral', 'lightgreen'][:len(overall_scores)])
        ax9.set_ylabel('Composite Score')
        ax9.set_title('Overall Method Performance')
        ax9.grid(True, alpha=0.3, axis='y')
        
        # Add value labels
        for bar, score in zip(bars, overall_scores):
            ax9.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{score:.3f}', ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    save_plot(fig, "parameter_optimization", "Skills Clustering Parameter Optimization")
    plt.show()

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main execution function for skills clustering parameter optimization"""
    print("🎯 SKILLS CLUSTERING - PARAMETER OPTIMIZATION")
    print("="*60)
    print("🔍 Systematic parameter testing for optimal skills clustering performance")
    print("📊 Testing multiple similarity measures and clustering algorithms")
    print("🏷️ Including taxonomy alignment validation")
    print()
    
    conn = connect_database()
    
    try:
        # Load data
        job_skills_df, cooccurrence_df, skill_metadata = load_skills_cooccurrence_data(conn)
        
        # Create similarity matrices
        similarity_matrices = create_similarity_matrices(cooccurrence_df)
        
        # Optimize DBSCAN parameters
        dbscan_results = optimize_dbscan_parameters(similarity_matrices, skill_metadata)
        
        # Optimize Hierarchical parameters
        hierarchical_results = optimize_hierarchical_parameters(similarity_matrices, skill_metadata)
        
        # Optimize K-means parameters
        kmeans_results = optimize_kmeans_parameters(similarity_matrices, skill_metadata)
        
        # Find optimal parameters
        recommendations = find_optimal_parameters(dbscan_results, hierarchical_results, kmeans_results)
        
        # Create visualizations
        create_skills_parameter_optimization_visualizations(
            dbscan_results, hierarchical_results, kmeans_results, recommendations
        )
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save all results
        dbscan_output = f"skills_dbscan_optimization_{timestamp}.csv"
        dbscan_results.to_csv(dbscan_output, index=False)
        print(f"\n💾 DBSCAN optimization results saved: {dbscan_output}")
        
        hierarchical_output = f"skills_hierarchical_optimization_{timestamp}.csv"
        hierarchical_results.to_csv(hierarchical_output, index=False)
        print(f"💾 Hierarchical optimization results saved: {hierarchical_output}")
        
        kmeans_output = f"skills_kmeans_optimization_{timestamp}.csv"
        kmeans_results.to_csv(kmeans_output, index=False)
        print(f"💾 K-means optimization results saved: {kmeans_output}")
        
        # Save recommendations
        recommendations_output = f"skills_clustering_recommendations_{timestamp}.txt"
        with open(recommendations_output, 'w') as f:
            f.write("SKILLS CLUSTERING - PARAMETER RECOMMENDATIONS\n")
            f.write("=" * 60 + "\n\n")
            
            for method_type, params in recommendations.items():
                if params:
                    f.write(f"OPTIMAL {method_type.upper()} PARAMETERS:\n")
                    for key, value in params.items():
                        f.write(f"{key}: {value}\n")
                    f.write("\n")
        
        print(f"💾 Parameter recommendations saved: {recommendations_output}")
        
        return {
            'dbscan_results': dbscan_results,
            'hierarchical_results': hierarchical_results,
            'kmeans_results': kmeans_results,
            'recommendations': recommendations,
            'similarity_matrices': similarity_matrices,
            'skill_metadata': skill_metadata
        }
        
    finally:
        conn.close()
        print(f"\n🔒 Database connection closed")

if __name__ == "__main__":
    print("🎯 SKILLS CLUSTERING - PARAMETER OPTIMIZATION")
    print("="*60)
    print("🔍 Data-driven parameter selection for optimal skills clustering")
    print("📊 Comprehensive evaluation across similarity measures and algorithms")
    print()
    
    results = main()
    
    print(f"\n🎉 PARAMETER OPTIMIZATION COMPLETE!")
    print(f"📁 Check generated files and plots for optimal parameter recommendations")
    print(f"💡 Use recommended parameters in production clustering (03b file)") 