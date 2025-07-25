#!/usr/bin/env python3
"""
JOB PROFILE CLUSTERING - PARAMETER OPTIMIZATION
===============================================

Systematic parameter optimization for job profile clustering to find optimal
clustering parameters before production runs. Uses silhouette analysis, elbow method,
and cluster stability metrics to recommend best parameters.

Purpose:
- Test DBSCAN eps/min_samples combinations systematically
- Apply elbow method for K-means cluster count optimization
- Calculate silhouette scores across parameter ranges
- Analyze cluster stability and validity metrics
- Provide visual parameter selection guides
- Generate automated optimal parameter recommendations

Philosophy: Data-driven parameter selection before production clustering

Usage:
    python 02a_job_profile_parameter_optimization.py
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
from sklearn.cluster import DBSCAN, KMeans
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from collections import defaultdict

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

class JobParameterOptimizationConfig:
    """Configuration for job profile clustering parameter optimization"""
    
    DATABASE_PATH = DATABASE_FILE
    
    # Defining skills configuration (from empirical tuning)
    DEFINING_SKILLS_PERCENTILE = 20   # Top 20% rarest skills per job
    GENTLE_MULTIPLIER = 1.05          # 5% boost per shared defining skill
    
    # DBSCAN parameter ranges to test
    DBSCAN_PARAMETER_GRID = {
        'eps': [0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7],
        'min_samples': [2, 3, 4, 5, 6, 7, 8, 10]
    }
    
    # K-means parameter ranges
    KMEANS_PARAMETER_GRID = {
        'n_clusters': list(range(3, 26))  # Test 3 to 25 clusters
    }
    
    # Evaluation settings
    EVALUATION_METRICS = [
        'silhouette_score',
        'calinski_harabasz_score', 
        'davies_bouldin_score',
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
        conn = sqlite3.connect(JobParameterOptimizationConfig.DATABASE_PATH)
        print(f"✅ Connected to database: {JobParameterOptimizationConfig.DATABASE_PATH}")
        return conn
    except sqlite3.OperationalError as e:
        raise FileNotFoundError(f"Could not connect to database: {e}")

def save_plot(fig, filename: str, title: Optional[str] = None):
    """Save plot with timestamp"""
    if title:
        fig.suptitle(title, fontsize=14, fontweight='bold')
    
    if JobParameterOptimizationConfig.SAVE_PLOTS:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        full_filename = f"job_param_opt_{filename}_{timestamp}.png"
        fig.savefig(full_filename, dpi=JobParameterOptimizationConfig.PLOT_DPI, bbox_inches='tight')
        print(f"   📊 Plot saved: {full_filename}")

# =============================================================================
# DATA LOADING (REUSED FROM PRODUCTION FILE)
# =============================================================================

def load_job_skill_data(conn) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load job profiles and their skills with prevalence information"""
    print("📚 Loading job profile and skill data...")
    
    job_skills_query = """
    SELECT 
        j.JobProfileID,
        j.JobProfile,
        j.JobFunction,
        j.JobSubFunction,
        j.JobCategory,
        j.ManagementLevel,
        js.Skill_ID,
        s.Skill_Name,
        s.Category as Skill_Category,
        s.SkillType
    FROM jobs j
    JOIN job_skills js ON j.JobProfileID = js.JobProfileID
    JOIN skills s ON js.Skill_ID = s.Skill_ID
    ORDER BY j.JobProfileID, s.Skill_Name
    """
    
    job_skills_df = pd.read_sql_query(job_skills_query, conn)
    
    # Calculate skill prevalence across all jobs
    total_jobs = job_skills_df['JobProfileID'].nunique()
    skill_prevalence = job_skills_df.groupby('Skill_Name').agg({
        'JobProfileID': 'nunique'
    }).reset_index()
    skill_prevalence['prevalence_percentage'] = (
        skill_prevalence['JobProfileID'] / total_jobs * 100
    )
    skill_prevalence = skill_prevalence.sort_values('prevalence_percentage')
    
    print(f"   → Job profiles: {job_skills_df['JobProfileID'].nunique():,}")
    print(f"   → Total job-skill relationships: {len(job_skills_df):,}")
    print(f"   → Unique skills: {job_skills_df['Skill_Name'].nunique():,}")
    
    return job_skills_df, skill_prevalence

def create_job_defining_skills(job_skills_df: pd.DataFrame, skill_prevalence: pd.DataFrame) -> Dict[str, Set[str]]:
    """Create job-specific defining skills using empirically-tuned parameters"""
    print(f"🎯 Creating job-specific defining skills (top {JobParameterOptimizationConfig.DEFINING_SKILLS_PERCENTILE}% rarest per job)...")
    
    job_defining_skills = {}
    skill_prevalence_dict = skill_prevalence.set_index('Skill_Name')['prevalence_percentage'].to_dict()
    
    for job_id, job_group in job_skills_df.groupby('JobProfileID'):
        job_skill_names = job_group['Skill_Name'].tolist()
        
        job_skills_with_prevalence = [
            (skill, skill_prevalence_dict.get(skill, 100))
            for skill in job_skill_names
        ]
        
        job_skills_with_prevalence.sort(key=lambda x: x[1])
        
        num_defining = max(1, len(job_skills_with_prevalence) * JobParameterOptimizationConfig.DEFINING_SKILLS_PERCENTILE // 100)
        defining_skills = [skill for skill, _ in job_skills_with_prevalence[:num_defining]]
        
        job_defining_skills[job_id] = set(defining_skills)
    
    total_jobs = len(job_defining_skills)
    total_defining_relationships = sum(len(skills) for skills in job_defining_skills.values())
    avg_defining_per_job = total_defining_relationships / total_jobs if total_jobs > 0 else 0
    
    print(f"   → Average defining skills per job: {avg_defining_per_job:.1f}")
    
    return job_defining_skills

def create_job_similarity_matrix(
    job_skills_df: pd.DataFrame, 
    job_defining_skills: Dict[str, Set[str]]
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Create enhanced job-to-job similarity matrix"""
    print("🔗 Creating enhanced job-to-job similarity matrix...")
    
    job_metadata = job_skills_df[['JobProfileID', 'JobProfile', 'JobFunction', 'JobSubFunction', 'JobCategory', 'ManagementLevel']].drop_duplicates()
    job_ids = job_metadata['JobProfileID'].tolist()
    
    job_to_skills = {}
    for job_id, job_group in job_skills_df.groupby('JobProfileID'):
        job_to_skills[job_id] = set(job_group['Skill_Name'])
    
    print(f"   → Calculating similarities for {len(job_ids):,} job profiles...")
    
    n_jobs = len(job_ids)
    enhanced_matrix = np.zeros((n_jobs, n_jobs))
    
    for i, job_a in enumerate(job_ids):
        for j, job_b in enumerate(job_ids):
            if i <= j:
                job_a_skills = job_to_skills[job_a]
                job_b_skills = job_to_skills[job_b]
                
                if job_a_skills and job_b_skills:
                    shared_skills = job_a_skills & job_b_skills
                    total_skills = job_a_skills | job_b_skills
                    baseline_sim = len(shared_skills) / len(total_skills)
                else:
                    baseline_sim = 0.0
                
                if i == j:
                    enhanced_sim = 1.0
                else:
                    job_a_defining = job_defining_skills.get(job_a, set())
                    job_b_defining = job_defining_skills.get(job_b, set())
                    all_defining = job_a_defining | job_b_defining
                    
                    shared_defining = [skill for skill in (job_a_skills & job_b_skills) if skill in all_defining]
                    
                    defining_skill_boost = len(shared_defining) * (JobParameterOptimizationConfig.GENTLE_MULTIPLIER - 1.0)
                    enhanced_sim = baseline_sim * (1.0 + defining_skill_boost)
                    enhanced_sim = min(1.0, enhanced_sim)
                
                enhanced_matrix[i, j] = enhanced_sim
                enhanced_matrix[j, i] = enhanced_sim
    
    enhanced_similarity_df = pd.DataFrame(enhanced_matrix, index=job_ids, columns=job_ids)
    
    print(f"   → Enhanced similarity matrix created")
    
    return enhanced_similarity_df, job_metadata

# =============================================================================
# PARAMETER OPTIMIZATION FUNCTIONS
# =============================================================================

def optimize_dbscan_parameters(
    similarity_df: pd.DataFrame,
    job_metadata: pd.DataFrame
) -> pd.DataFrame:
    """
    Systematically test DBSCAN parameters and evaluate clustering quality
    
    Returns:
        DataFrame with parameter combinations and evaluation metrics
    """
    print("\n🔍 OPTIMIZING DBSCAN PARAMETERS")
    print("="*50)
    
    distance_matrix = 1 - similarity_df.values
    distance_matrix = np.maximum(distance_matrix, 0)
    
    results = []
    total_combinations = len(JobParameterOptimizationConfig.DBSCAN_PARAMETER_GRID['eps']) * len(JobParameterOptimizationConfig.DBSCAN_PARAMETER_GRID['min_samples'])
    
    print(f"   → Testing {total_combinations} parameter combinations...")
    
    combination_count = 0
    for eps in JobParameterOptimizationConfig.DBSCAN_PARAMETER_GRID['eps']:
        for min_samples in JobParameterOptimizationConfig.DBSCAN_PARAMETER_GRID['min_samples']:
            combination_count += 1
            
            if combination_count % 20 == 0:
                print(f"   → Progress: {combination_count}/{total_combinations} ({combination_count/total_combinations*100:.1f}%)")
            
            # Perform clustering
            dbscan = DBSCAN(eps=eps, min_samples=min_samples, metric='precomputed')
            labels = dbscan.fit_predict(distance_matrix)
            
            # Calculate metrics
            n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
            noise_points = list(labels).count(-1)
            noise_ratio = noise_points / len(labels)
            
            # Initialize metrics
            silhouette = None
            calinski_harabasz = None
            davies_bouldin = None
            
            # Calculate quality metrics if we have valid clusters
            if n_clusters > 1 and noise_points < len(labels):
                try:
                    # Use only non-noise points for evaluation
                    non_noise_mask = labels != -1
                    if np.sum(non_noise_mask) > 1 and len(set(labels[non_noise_mask])) > 1:
                        non_noise_distance = distance_matrix[non_noise_mask][:, non_noise_mask]
                        non_noise_labels = labels[non_noise_mask]
                        
                        silhouette = silhouette_score(non_noise_distance, non_noise_labels, metric='precomputed')
                        
                        # For other metrics, use similarity matrix (not distance)
                        non_noise_similarity = similarity_df.values[non_noise_mask][:, non_noise_mask]
                        calinski_harabasz = calinski_harabasz_score(non_noise_similarity, non_noise_labels)
                        davies_bouldin = davies_bouldin_score(non_noise_similarity, non_noise_labels)
                        
                except Exception as e:
                    pass  # Keep metrics as None
            
            results.append({
                'eps': eps,
                'min_samples': min_samples,
                'n_clusters': n_clusters,
                'noise_points': noise_points,
                'noise_ratio': noise_ratio,
                'silhouette_score': silhouette,
                'calinski_harabasz_score': calinski_harabasz,
                'davies_bouldin_score': davies_bouldin
            })
    
    results_df = pd.DataFrame(results)
    
    print(f"   → Completed parameter optimization")
    print(f"   → Valid clustering results: {results_df['silhouette_score'].notna().sum()}/{len(results_df)}")
    
    return results_df

def optimize_kmeans_parameters(
    similarity_df: pd.DataFrame,
    job_metadata: pd.DataFrame
) -> pd.DataFrame:
    """
    Apply elbow method and silhouette analysis for K-means optimization
    
    Returns:
        DataFrame with K-means evaluation results
    """
    print("\n🔍 OPTIMIZING K-MEANS PARAMETERS (ELBOW METHOD)")
    print("="*50)
    
    try:
        # Use PCA to reduce dimensionality for K-means
        pca = PCA(n_components=min(50, similarity_df.shape[0]-1))
        similarity_features = pca.fit_transform(similarity_df.values)
        
        # Standardize features to improve numerical stability
        scaler = StandardScaler()
        similarity_features = scaler.fit_transform(similarity_features)
        
        print(f"   → Reduced dimensionality to {similarity_features.shape[1]} components")
        print(f"   → Explained variance ratio: {pca.explained_variance_ratio_.sum():.3f}")
        print(f"   → Features standardized for numerical stability")
        
        results = []
        
        # Test smaller batches to avoid Windows subprocess issues
        cluster_ranges = JobParameterOptimizationConfig.KMEANS_PARAMETER_GRID['n_clusters']
        successful_tests = 0
        
        for i, n_clusters in enumerate(cluster_ranges):
            try:
                print(f"   → Testing {n_clusters} clusters ({i+1}/{len(cluster_ranges)})")
                
                # Use more conservative parameters to avoid numerical issues
                kmeans = KMeans(
                    n_clusters=n_clusters, 
                    random_state=42, 
                    n_init=5,  # Reduced from 10 for stability
                    max_iter=100,  # Add max_iter limit
                    tol=1e-3,  # Slightly larger tolerance
                    algorithm='lloyd'  # Use explicit algorithm
                )
                
                labels = kmeans.fit_predict(similarity_features)
                
                # Calculate metrics
                inertia = kmeans.inertia_
                silhouette = silhouette_score(similarity_features, labels)
                calinski_harabasz = calinski_harabasz_score(similarity_features, labels)
                davies_bouldin = davies_bouldin_score(similarity_features, labels)
                
                results.append({
                    'n_clusters': n_clusters,
                    'inertia': inertia,
                    'silhouette_score': silhouette,
                    'calinski_harabasz_score': calinski_harabasz,
                    'davies_bouldin_score': davies_bouldin
                })
                
                successful_tests += 1
                
            except Exception as e:
                print(f"   → Error with n_clusters={n_clusters}: {str(e)[:100]}...")
                continue
        
        results_df = pd.DataFrame(results)
        
        print(f"   → Completed K-means optimization: {successful_tests}/{len(cluster_ranges)} successful tests")
        
        if len(results_df) == 0:
            print("   ⚠️ No successful K-means tests - skipping K-means optimization")
            # Return empty DataFrame with expected columns
            return pd.DataFrame(columns=['n_clusters', 'inertia', 'silhouette_score', 'calinski_harabasz_score', 'davies_bouldin_score'])
        
        return results_df
        
    except Exception as e:
        print(f"   ❌ K-means optimization failed completely: {str(e)[:100]}...")
        print("   → Skipping K-means optimization")
        # Return empty DataFrame with expected columns
        return pd.DataFrame(columns=['n_clusters', 'inertia', 'silhouette_score', 'calinski_harabasz_score', 'davies_bouldin_score'])

def find_optimal_parameters(
    dbscan_results: pd.DataFrame,
    kmeans_results: pd.DataFrame
) -> Dict[str, Any]:
    """
    Analyze results and recommend optimal parameters
    
    Returns:
        Dict with optimal parameter recommendations
    """
    print("\n🏆 FINDING OPTIMAL PARAMETERS")
    print("="*50)
    
    recommendations = {}
    
    # DBSCAN optimization
    valid_dbscan = dbscan_results[dbscan_results['silhouette_score'].notna()].copy()
    
    if len(valid_dbscan) > 0:
        # Score DBSCAN results (balance silhouette score and reasonable cluster count)
        valid_dbscan['cluster_score'] = np.where(
            (valid_dbscan['n_clusters'] >= 5) & (valid_dbscan['n_clusters'] <= 20),
            1.0,  # Ideal range
            0.8   # Penalize extreme cluster counts
        )
        
        valid_dbscan['noise_score'] = np.where(
            valid_dbscan['noise_ratio'] <= 0.3,
            1.0,  # Low noise is good
            1.0 - valid_dbscan['noise_ratio']  # Penalize high noise
        )
        
        valid_dbscan['composite_score'] = (
            0.5 * valid_dbscan['silhouette_score'] +
            0.3 * valid_dbscan['cluster_score'] +
            0.2 * valid_dbscan['noise_score']
        )
        
        best_dbscan = valid_dbscan.loc[valid_dbscan['composite_score'].idxmax()]
        
        recommendations['dbscan'] = {
            'eps': best_dbscan['eps'],
            'min_samples': best_dbscan['min_samples'],
            'expected_clusters': best_dbscan['n_clusters'],
            'expected_noise_ratio': best_dbscan['noise_ratio'],
            'silhouette_score': best_dbscan['silhouette_score'],
            'composite_score': best_dbscan['composite_score']
        }
        
        print(f"🥇 OPTIMAL DBSCAN PARAMETERS:")
        print(f"   → eps: {best_dbscan['eps']}")
        print(f"   → min_samples: {best_dbscan['min_samples']}")
        print(f"   → Expected clusters: {best_dbscan['n_clusters']}")
        print(f"   → Expected noise ratio: {best_dbscan['noise_ratio']:.1%}")
        print(f"   → Silhouette score: {best_dbscan['silhouette_score']:.3f}")
        print(f"   → Composite score: {best_dbscan['composite_score']:.3f}")
    else:
        print("❌ No valid DBSCAN parameters found")
        recommendations['dbscan'] = None
    
    # K-means optimization (elbow method + silhouette)
    if len(kmeans_results) > 0 and 'inertia' in kmeans_results.columns:
        try:
            # Find elbow point using rate of change in inertia
            kmeans_results = kmeans_results.sort_values('n_clusters')
            
            # Calculate rate of change in inertia
            inertia_values = kmeans_results['inertia'].values
            if len(inertia_values) >= 3:  # Need at least 3 points for second derivative
                inertia_diff = np.diff(inertia_values)
                inertia_diff_2 = np.diff(inertia_diff)
                
                # Find elbow (maximum second derivative)
                if len(inertia_diff_2) > 0:
                    elbow_idx = np.argmax(inertia_diff_2) + 2  # +2 due to double diff
                    elbow_clusters = kmeans_results.iloc[elbow_idx]['n_clusters']
                else:
                    elbow_clusters = None
            else:
                elbow_clusters = None
            
            # Find best silhouette score
            best_silhouette_idx = kmeans_results['silhouette_score'].idxmax()
            best_silhouette = kmeans_results.loc[best_silhouette_idx]
            
            recommendations['kmeans'] = {
                'elbow_method_clusters': elbow_clusters,
                'best_silhouette_clusters': best_silhouette['n_clusters'],
                'best_silhouette_score': best_silhouette['silhouette_score'],
                'recommended_clusters': elbow_clusters if elbow_clusters else best_silhouette['n_clusters']
            }
            
            print(f"\n🥇 OPTIMAL K-MEANS PARAMETERS:")
            print(f"   → Elbow method suggests: {elbow_clusters} clusters")
            print(f"   → Best silhouette score at: {best_silhouette['n_clusters']} clusters ({best_silhouette['silhouette_score']:.3f})")
            print(f"   → Recommended: {recommendations['kmeans']['recommended_clusters']} clusters")
            
        except Exception as e:
            print(f"❌ Error processing K-means results: {str(e)[:50]}...")
            recommendations['kmeans'] = None
    else:
        print("❌ No valid K-means parameters found")
        recommendations['kmeans'] = None
    
    return recommendations

# =============================================================================
# VISUALIZATION FUNCTIONS
# =============================================================================

def create_parameter_optimization_visualizations(
    dbscan_results: pd.DataFrame,
    kmeans_results: pd.DataFrame,
    recommendations: Dict[str, Any]
) -> None:
    """Create comprehensive parameter optimization visualizations"""
    print("\n📈 Creating parameter optimization visualizations...")
    
    # Create figure with subplots
    fig = plt.figure(figsize=(20, 16))
    
    # 1. DBSCAN Parameter Heatmap (Silhouette Score)
    ax1 = plt.subplot(2, 3, 1)
    valid_dbscan = dbscan_results[dbscan_results['silhouette_score'].notna()]
    
    if len(valid_dbscan) > 0:
        pivot_silhouette = valid_dbscan.pivot(index='min_samples', columns='eps', values='silhouette_score')
        sns.heatmap(pivot_silhouette, annot=True, fmt='.3f', cmap='viridis', ax=ax1)
        ax1.set_title('DBSCAN Silhouette Score Heatmap')
        ax1.set_xlabel('eps')
        ax1.set_ylabel('min_samples')
        
        # Mark optimal point
        if recommendations['dbscan']:
            opt_eps = recommendations['dbscan']['eps']
            opt_min = recommendations['dbscan']['min_samples']
            # Find position in heatmap
            eps_pos = list(pivot_silhouette.columns).index(opt_eps)
            min_pos = list(pivot_silhouette.index).index(opt_min)
            from matplotlib.patches import Rectangle
            ax1.add_patch(Rectangle((eps_pos, min_pos), 1, 1, fill=False, edgecolor='red', lw=3))
    
    # 2. DBSCAN Cluster Count Heatmap
    ax2 = plt.subplot(2, 3, 2)
    if len(valid_dbscan) > 0:
        pivot_clusters = dbscan_results.pivot(index='min_samples', columns='eps', values='n_clusters')
        sns.heatmap(pivot_clusters, annot=True, fmt='d', cmap='plasma', ax=ax2)
        ax2.set_title('DBSCAN Number of Clusters')
        ax2.set_xlabel('eps')
        ax2.set_ylabel('min_samples')
    
    # 3. DBSCAN Noise Ratio Heatmap
    ax3 = plt.subplot(2, 3, 3)
    if len(valid_dbscan) > 0:
        pivot_noise = dbscan_results.pivot(index='min_samples', columns='eps', values='noise_ratio')
        sns.heatmap(pivot_noise, annot=True, fmt='.2f', cmap='Reds', ax=ax3)
        ax3.set_title('DBSCAN Noise Ratio')
        ax3.set_xlabel('eps')
        ax3.set_ylabel('min_samples')
    
    # 4. K-means Elbow Curve
    ax4 = plt.subplot(2, 3, 4)
    if len(kmeans_results) > 0:
        ax4.plot(kmeans_results['n_clusters'], kmeans_results['inertia'], 'bo-', linewidth=2, markersize=8)
        ax4.set_xlabel('Number of Clusters')
        ax4.set_ylabel('Inertia (Within-cluster sum of squares)')
        ax4.set_title('K-means Elbow Curve')
        ax4.grid(True, alpha=0.3)
        
        # Mark elbow point
        if recommendations['kmeans'] and recommendations['kmeans']['elbow_method_clusters']:
            elbow_k = recommendations['kmeans']['elbow_method_clusters']
            elbow_inertia = kmeans_results[kmeans_results['n_clusters'] == elbow_k]['inertia'].iloc[0]
            ax4.axvline(x=elbow_k, color='red', linestyle='--', linewidth=2, label=f'Elbow at k={elbow_k}')
            ax4.legend()
    
    # 5. K-means Silhouette Score
    ax5 = plt.subplot(2, 3, 5)
    if len(kmeans_results) > 0:
        ax5.plot(kmeans_results['n_clusters'], kmeans_results['silhouette_score'], 'go-', linewidth=2, markersize=8)
        ax5.set_xlabel('Number of Clusters')
        ax5.set_ylabel('Silhouette Score')
        ax5.set_title('K-means Silhouette Analysis')
        ax5.grid(True, alpha=0.3)
        
        # Mark best silhouette
        if recommendations['kmeans']:
            best_k = recommendations['kmeans']['best_silhouette_clusters']
            best_score = recommendations['kmeans']['best_silhouette_score']
            ax5.axvline(x=best_k, color='red', linestyle='--', linewidth=2, label=f'Best at k={best_k}')
            ax5.legend()
    
    # 6. Method Comparison
    ax6 = plt.subplot(2, 3, 6)
    method_names = []
    method_scores = []
    
    if recommendations['dbscan']:
        method_names.append(f"DBSCAN\n(eps={recommendations['dbscan']['eps']}, min={recommendations['dbscan']['min_samples']})")
        method_scores.append(recommendations['dbscan']['silhouette_score'])
    
    if recommendations['kmeans']:
        method_names.append(f"K-means\n(k={recommendations['kmeans']['recommended_clusters']})")
        method_scores.append(recommendations['kmeans']['best_silhouette_score'])
    
    if method_names:
        bars = ax6.bar(method_names, method_scores, color=['skyblue', 'lightcoral'][:len(method_names)])
        ax6.set_ylabel('Silhouette Score')
        ax6.set_title('Optimal Methods Comparison')
        ax6.grid(True, alpha=0.3, axis='y')
        
        # Add value labels on bars
        for bar, score in zip(bars, method_scores):
            ax6.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{score:.3f}', ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    save_plot(fig, "parameter_optimization", "Job Profile Clustering Parameter Optimization")
    plt.show()

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main execution function for job profile clustering parameter optimization"""
    print("🎯 JOB PROFILE CLUSTERING - PARAMETER OPTIMIZATION")
    print("="*60)
    print("🔍 Systematic parameter testing for optimal clustering performance")
    print("📊 Using silhouette analysis, elbow method, and cluster stability metrics")
    print(f"⚙️ Enhanced similarity with {JobParameterOptimizationConfig.DEFINING_SKILLS_PERCENTILE}% percentile, {JobParameterOptimizationConfig.GENTLE_MULTIPLIER:.2f}x multiplier")
    print()
    
    conn = connect_database()
    
    try:
        # Load data
        job_skills_df, skill_prevalence = load_job_skill_data(conn)
        
        # Create defining skills
        job_defining_skills = create_job_defining_skills(job_skills_df, skill_prevalence)
        
        # Create similarity matrix
        similarity_df, job_metadata = create_job_similarity_matrix(job_skills_df, job_defining_skills)
        
        # Optimize DBSCAN parameters
        dbscan_results = optimize_dbscan_parameters(similarity_df, job_metadata)
        
        # Optimize K-means parameters
        kmeans_results = optimize_kmeans_parameters(similarity_df, job_metadata)
        
        # Find optimal parameters
        recommendations = find_optimal_parameters(dbscan_results, kmeans_results)
        
        # Create visualizations
        create_parameter_optimization_visualizations(dbscan_results, kmeans_results, recommendations)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save DBSCAN results
        dbscan_output = f"job_dbscan_optimization_{timestamp}.csv"
        dbscan_results.to_csv(dbscan_output, index=False)
        print(f"\n💾 DBSCAN optimization results saved: {dbscan_output}")
        
        # Save K-means results
        kmeans_output = f"job_kmeans_optimization_{timestamp}.csv"
        kmeans_results.to_csv(kmeans_output, index=False)
        print(f"💾 K-means optimization results saved: {kmeans_output}")
        
        # Save recommendations
        recommendations_output = f"job_clustering_recommendations_{timestamp}.txt"
        with open(recommendations_output, 'w') as f:
            f.write("JOB PROFILE CLUSTERING - PARAMETER RECOMMENDATIONS\n")
            f.write("=" * 60 + "\n\n")
            
            if recommendations['dbscan']:
                f.write("OPTIMAL DBSCAN PARAMETERS:\n")
                f.write(f"eps: {recommendations['dbscan']['eps']}\n")
                f.write(f"min_samples: {recommendations['dbscan']['min_samples']}\n")
                f.write(f"Expected clusters: {recommendations['dbscan']['expected_clusters']}\n")
                f.write(f"Expected noise ratio: {recommendations['dbscan']['expected_noise_ratio']:.1%}\n")
                f.write(f"Silhouette score: {recommendations['dbscan']['silhouette_score']:.3f}\n\n")
            
            if recommendations['kmeans']:
                f.write("OPTIMAL K-MEANS PARAMETERS:\n")
                f.write(f"Recommended clusters: {recommendations['kmeans']['recommended_clusters']}\n")
                f.write(f"Elbow method suggests: {recommendations['kmeans']['elbow_method_clusters']}\n")
                f.write(f"Best silhouette at: {recommendations['kmeans']['best_silhouette_clusters']} clusters\n")
                f.write(f"Best silhouette score: {recommendations['kmeans']['best_silhouette_score']:.3f}\n")
        
        print(f"💾 Parameter recommendations saved: {recommendations_output}")
        
        return {
            'dbscan_results': dbscan_results,
            'kmeans_results': kmeans_results,
            'recommendations': recommendations,
            'similarity_df': similarity_df,
            'job_metadata': job_metadata
        }
        
    finally:
        conn.close()
        print(f"\n🔒 Database connection closed")

if __name__ == "__main__":
    print("🎯 JOB PROFILE CLUSTERING - PARAMETER OPTIMIZATION")
    print("="*60)
    print("🔍 Data-driven parameter selection for optimal job clustering")
    print("📊 Comprehensive evaluation of DBSCAN and K-means parameters")
    print()
    
    results = main()
    
    print(f"\n🎉 PARAMETER OPTIMIZATION COMPLETE!")
    print(f"📁 Check generated files and plots for optimal parameter recommendations")
    print(f"💡 Use recommended parameters in production clustering (02b file)") 