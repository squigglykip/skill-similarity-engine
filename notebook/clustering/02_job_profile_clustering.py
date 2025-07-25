#!/usr/bin/env python3
"""
JOB PROFILE CLUSTERING EXPLORATION
=================================

Clustering job profiles based on their skill portfolios using the empirically-tuned
defining skills methodology (20% percentile + 1.05x multiplier).

This complements skill co-occurrence analysis by finding natural job archetypes
based on enhanced similarity calculations.

Purpose:
- Cluster job profiles (not skills) based on enhanced skill portfolio similarity
- Use defining skills weighting to improve clustering quality
- Find natural job archetypes and career pathway clusters
- Compare basic vs enhanced similarity clustering results

Philosophy: Job archetypes emerge from skill portfolio patterns with defining skills emphasis

Usage:
    python job_profile_clustering_exploration.py
"""

import pandas as pd
import numpy as np
import sqlite3
import warnings
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Set, Any
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import DBSCAN, KMeans
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import silhouette_score, calinski_harabasz_score
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import umap

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

class JobClusteringConfig:
    """Configuration for job profile clustering exploration"""
    
    DATABASE_PATH = DATABASE_FILE
    
    # Defining skills configuration (from empirical tuning)
    DEFINING_SKILLS_PERCENTILE = 20   # Top 20% rarest skills per job
    GENTLE_MULTIPLIER = 1.05          # 5% boost per shared defining skill
    
    # Clustering parameters to test
    DBSCAN_PARAMS = [
        {'eps': 0.3, 'min_samples': 3},
        {'eps': 0.4, 'min_samples': 3}, 
        {'eps': 0.5, 'min_samples': 3},
        {'eps': 0.3, 'min_samples': 5},
        {'eps': 0.4, 'min_samples': 5},
        {'eps': 0.5, 'min_samples': 5},
    ]
    
    KMEANS_PARAMS = [
        {'n_clusters': 8},
        {'n_clusters': 10},
        {'n_clusters': 12},
        {'n_clusters': 15},
        {'n_clusters': 20},
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
        conn = sqlite3.connect(JobClusteringConfig.DATABASE_PATH)
        print(f"✅ Connected to database: {JobClusteringConfig.DATABASE_PATH}")
        return conn
    except sqlite3.OperationalError as e:
        raise FileNotFoundError(f"Could not connect to database: {e}")

def save_plot(fig, filename: str, title: Optional[str] = None):
    """Save plot with timestamp"""
    if title:
        fig.suptitle(title, fontsize=14, fontweight='bold')
    
    if JobClusteringConfig.SAVE_PLOTS:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        full_filename = f"job_clustering_{filename}_{timestamp}.png"
        fig.savefig(full_filename, dpi=JobClusteringConfig.PLOT_DPI, bbox_inches='tight')
        print(f"   📊 Plot saved: {full_filename}")

# =============================================================================
# DATA LOADING AND PREPROCESSING
# =============================================================================

def load_job_skill_data(conn) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load job profiles and their skills with prevalence information
    
    Returns:
        Tuple of (job_skills_df, skill_prevalence_df)
    """
    print("📚 Loading job profile and skill data...")
    
    # Load job-skill relationships with context
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
    print(f"   → Skills per job (avg): {len(job_skills_df) / job_skills_df['JobProfileID'].nunique():.1f}")
    
    return job_skills_df, skill_prevalence

def create_job_defining_skills(job_skills_df: pd.DataFrame, skill_prevalence: pd.DataFrame) -> Dict[str, Set[str]]:
    """
    Create job-specific defining skills using empirically-tuned parameters
    
    Returns:
        Dict mapping JobProfileID to Set of defining skill names
    """
    print(f"🎯 Creating job-specific defining skills (top {JobClusteringConfig.DEFINING_SKILLS_PERCENTILE}% rarest per job)...")
    
    job_defining_skills = {}
    
    # Create skill prevalence lookup
    skill_prevalence_dict = skill_prevalence.set_index('Skill_Name')['prevalence_percentage'].to_dict()
    
    # Group by job and find defining skills
    for job_id, job_group in job_skills_df.groupby('JobProfileID'):
        job_skill_names = job_group['Skill_Name'].tolist()
        
        # Get prevalence for this job's skills
        job_skills_with_prevalence = [
            (skill, skill_prevalence_dict.get(skill, 100))  # Default to high prevalence if missing
            for skill in job_skill_names
        ]
        
        # Sort by prevalence (ascending = rarest first)
        job_skills_with_prevalence.sort(key=lambda x: x[1])
        
        # Take top X% rarest skills for this job
        num_defining = max(1, len(job_skills_with_prevalence) * JobClusteringConfig.DEFINING_SKILLS_PERCENTILE // 100)
        defining_skills = [skill for skill, _ in job_skills_with_prevalence[:num_defining]]
        
        job_defining_skills[job_id] = set(defining_skills)
    
    # Calculate summary statistics
    total_jobs = len(job_defining_skills)
    total_defining_relationships = sum(len(skills) for skills in job_defining_skills.values())
    avg_defining_per_job = total_defining_relationships / total_jobs if total_jobs > 0 else 0
    
    print(f"   → Job profiles with defining skills: {total_jobs:,}")
    print(f"   → Total defining skill relationships: {total_defining_relationships:,}")
    print(f"   → Average defining skills per job: {avg_defining_per_job:.1f}")
    
    return job_defining_skills

def create_job_similarity_matrix(
    job_skills_df: pd.DataFrame, 
    job_defining_skills: Dict[str, Set[str]]
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Create job-to-job similarity matrices (baseline and enhanced)
    
    Returns:
        Tuple of (baseline_similarity_df, enhanced_similarity_df, job_metadata_df)
    """
    print("🔗 Creating job-to-job similarity matrices...")
    
    # Get unique job profiles
    job_metadata = job_skills_df[['JobProfileID', 'JobProfile', 'JobFunction', 'JobSubFunction', 'JobCategory', 'ManagementLevel']].drop_duplicates()
    job_ids = job_metadata['JobProfileID'].tolist()
    
    # Create job-to-skills mapping
    job_to_skills = {}
    for job_id, job_group in job_skills_df.groupby('JobProfileID'):
        job_to_skills[job_id] = set(job_group['Skill_Name'])
    
    print(f"   → Calculating similarities for {len(job_ids):,} job profiles...")
    print(f"   → Total comparisons: {len(job_ids) * (len(job_ids) - 1) // 2:,} unique pairs")
    
    # Initialize similarity matrices
    n_jobs = len(job_ids)
    baseline_matrix = np.zeros((n_jobs, n_jobs))
    enhanced_matrix = np.zeros((n_jobs, n_jobs))
    
    # Calculate pairwise similarities
    for i, job_a in enumerate(job_ids):
        for j, job_b in enumerate(job_ids):
            if i <= j:  # Only calculate upper triangle + diagonal
                job_a_skills = job_to_skills[job_a]
                job_b_skills = job_to_skills[job_b]
                
                # Baseline similarity (Jaccard)
                if job_a_skills and job_b_skills:
                    shared_skills = job_a_skills & job_b_skills
                    total_skills = job_a_skills | job_b_skills
                    baseline_sim = len(shared_skills) / len(total_skills)
                else:
                    baseline_sim = 0.0
                
                # Enhanced similarity with defining skills boost
                if i == j:  # Self-similarity
                    enhanced_sim = 1.0
                else:
                    job_a_defining = job_defining_skills.get(job_a, set())
                    job_b_defining = job_defining_skills.get(job_b, set())
                    all_defining = job_a_defining | job_b_defining
                    
                    shared_defining = [skill for skill in (job_a_skills & job_b_skills) if skill in all_defining]
                    
                    # Apply gentle multiplier
                    defining_skill_boost = len(shared_defining) * (JobClusteringConfig.GENTLE_MULTIPLIER - 1.0)
                    enhanced_sim = baseline_sim * (1.0 + defining_skill_boost)
                    enhanced_sim = min(1.0, enhanced_sim)  # Cap at 1.0
                
                # Fill both triangles (symmetric matrix)
                baseline_matrix[i, j] = baseline_sim
                baseline_matrix[j, i] = baseline_sim
                enhanced_matrix[i, j] = enhanced_sim
                enhanced_matrix[j, i] = enhanced_sim
    
    # Convert to DataFrames with job IDs as indices
    baseline_similarity_df = pd.DataFrame(baseline_matrix, index=job_ids, columns=job_ids)
    enhanced_similarity_df = pd.DataFrame(enhanced_matrix, index=job_ids, columns=job_ids)
    
    # Calculate improvement statistics
    improvements = enhanced_matrix - baseline_matrix
    avg_improvement = np.mean(improvements[np.triu_indices_from(improvements, k=1)])
    positive_improvements = np.sum(improvements > 0) - len(job_ids)  # Exclude diagonal
    total_comparisons = len(job_ids) * (len(job_ids) - 1)
    
    print(f"   → Average similarity improvement: {avg_improvement:.4f}")
    print(f"   → Positive improvements: {positive_improvements:,}/{total_comparisons:,} ({positive_improvements/total_comparisons*100:.1f}%)")
    print(f"   → Using {JobClusteringConfig.GENTLE_MULTIPLIER:.2f}x multiplier for defining skills")
    
    return baseline_similarity_df, enhanced_similarity_df, job_metadata

# =============================================================================
# CLUSTERING ANALYSIS
# =============================================================================

def perform_clustering_comparison(
    baseline_similarity_df: pd.DataFrame,
    enhanced_similarity_df: pd.DataFrame,
    job_metadata: pd.DataFrame
) -> Dict[str, Any]:
    """
    Compare clustering results between baseline and enhanced similarity matrices
    
    Returns:
        Dict with clustering results and evaluation metrics
    """
    print("\n🔍 PERFORMING CLUSTERING COMPARISON")
    print("="*50)
    
    # Convert similarity to distance for clustering
    baseline_distance = 1 - baseline_similarity_df.values
    enhanced_distance = 1 - enhanced_similarity_df.values
    
    # Ensure valid distance matrices (handle negative values from floating point precision)
    baseline_distance = np.maximum(baseline_distance, 0)
    enhanced_distance = np.maximum(enhanced_distance, 0)
    
    clustering_results = {
        'baseline': {},
        'enhanced': {},
        'comparison': {}
    }
    
    # Test DBSCAN parameters
    print("\n📊 Testing DBSCAN Parameters:")
    print("-" * 40)
    
    for params in JobClusteringConfig.DBSCAN_PARAMS:
        eps = params['eps']
        min_samples = params['min_samples']
        
        print(f"\n🔧 DBSCAN: eps={eps}, min_samples={min_samples}")
        
        # Baseline clustering
        dbscan_baseline = DBSCAN(eps=eps, min_samples=min_samples, metric='precomputed')
        baseline_labels = dbscan_baseline.fit_predict(baseline_distance)
        
        # Enhanced clustering  
        dbscan_enhanced = DBSCAN(eps=eps, min_samples=min_samples, metric='precomputed')
        enhanced_labels = dbscan_enhanced.fit_predict(enhanced_distance)
        
        # Calculate metrics
        baseline_n_clusters = len(set(baseline_labels)) - (1 if -1 in baseline_labels else 0)
        enhanced_n_clusters = len(set(enhanced_labels)) - (1 if -1 in enhanced_labels else 0)
        baseline_noise = list(baseline_labels).count(-1)
        enhanced_noise = list(enhanced_labels).count(-1)
        
        print(f"   Baseline: {baseline_n_clusters} clusters, {baseline_noise} noise points")
        print(f"   Enhanced: {enhanced_n_clusters} clusters, {enhanced_noise} noise points")
        
        # Store results
        param_key = f"eps_{eps}_min_{min_samples}"
        clustering_results['baseline'][param_key] = {
            'labels': baseline_labels,
            'n_clusters': baseline_n_clusters,
            'noise_points': baseline_noise,
            'params': params
        }
        clustering_results['enhanced'][param_key] = {
            'labels': enhanced_labels,
            'n_clusters': enhanced_n_clusters,
            'noise_points': enhanced_noise,
            'params': params
        }
    
    # Test K-Means parameters (using similarity directly)
    print(f"\n📊 Testing K-Means Parameters:")
    print("-" * 40)
    
    for params in JobClusteringConfig.KMEANS_PARAMS:
        n_clusters = params['n_clusters']
        
        print(f"\n🔧 K-Means: n_clusters={n_clusters}")
        
        # Use similarity matrices directly (convert to features via PCA)
        pca = PCA(n_components=min(50, baseline_similarity_df.shape[0]-1))  # Reduce dimensionality
        
        baseline_features = pca.fit_transform(baseline_similarity_df.values)
        enhanced_features = pca.fit_transform(enhanced_similarity_df.values)
        
        # Baseline clustering
        kmeans_baseline = KMeans(n_clusters=n_clusters, random_state=42)
        baseline_labels = kmeans_baseline.fit_predict(baseline_features)
        
        # Enhanced clustering
        kmeans_enhanced = KMeans(n_clusters=n_clusters, random_state=42)
        enhanced_labels = kmeans_enhanced.fit_predict(enhanced_features)
        
        # Calculate silhouette scores
        try:
            baseline_silhouette = silhouette_score(baseline_features, baseline_labels)
            enhanced_silhouette = silhouette_score(enhanced_features, enhanced_labels)
            print(f"   Baseline silhouette: {baseline_silhouette:.3f}")
            print(f"   Enhanced silhouette: {enhanced_silhouette:.3f}")
        except:
            baseline_silhouette = None
            enhanced_silhouette = None
            print(f"   Could not calculate silhouette scores")
        
        # Store results
        param_key = f"k_{n_clusters}"
        clustering_results['baseline'][param_key] = {
            'labels': baseline_labels,
            'n_clusters': n_clusters,
            'silhouette_score': baseline_silhouette,
            'params': params
        }
        clustering_results['enhanced'][param_key] = {
            'labels': enhanced_labels,
            'n_clusters': n_clusters,
            'silhouette_score': enhanced_silhouette,
            'params': params
        }
    
    return clustering_results

def analyze_best_clustering(
    clustering_results: Dict[str, Any],
    job_metadata: pd.DataFrame,
    job_skills_df: pd.DataFrame
) -> None:
    """Analyze the best clustering result in detail"""
    print("\n🏆 BEST CLUSTERING ANALYSIS")
    print("="*50)
    
    # Find best DBSCAN result (fewest noise points, reasonable cluster count)
    best_dbscan_key = None
    best_dbscan_score = float('inf')
    
    for key, result in clustering_results['enhanced'].items():
        if key.startswith('eps_'):
            # Score based on noise ratio and cluster count reasonableness
            noise_ratio = result['noise_points'] / len(job_metadata)
            n_clusters = result['n_clusters']
            
            # Penalize too many noise points and extreme cluster counts
            score = noise_ratio * 2 + abs(n_clusters - 10) * 0.1  # Target ~10 clusters
            
            if score < best_dbscan_score and n_clusters > 0:
                best_dbscan_score = score
                best_dbscan_key = key
    
    if best_dbscan_key:
        print(f"🥇 Best DBSCAN Configuration: {best_dbscan_key}")
        best_result = clustering_results['enhanced'][best_dbscan_key]
        labels = best_result['labels']
        
        # Add cluster labels to job metadata
        analysis_df = job_metadata.copy()
        analysis_df['cluster'] = labels
        
        print(f"   → Clusters: {best_result['n_clusters']}")
        print(f"   → Noise points: {best_result['noise_points']}")
        print(f"   → Parameters: {best_result['params']}")
        
        # Analyze clusters by job function
        print(f"\n📊 Cluster Analysis by Job Function:")
        cluster_analysis = analysis_df.groupby(['cluster', 'JobFunction']).size().unstack(fill_value=0)
        
        for cluster_id in sorted(analysis_df['cluster'].unique()):
            if cluster_id == -1:
                print(f"\n   🔸 Noise Points ({sum(labels == -1)} jobs):")
                noise_jobs = analysis_df[analysis_df['cluster'] == -1]
                function_counts = noise_jobs['JobFunction'].value_counts().head(5)
                for func, count in function_counts.items():
                    print(f"     • {func}: {count} jobs")
            else:
                cluster_jobs = analysis_df[analysis_df['cluster'] == cluster_id]
                print(f"\n   🔹 Cluster {cluster_id} ({len(cluster_jobs)} jobs):")
                function_counts = cluster_jobs['JobFunction'].value_counts().head(3)
                for func, count in function_counts.items():
                    print(f"     • {func}: {count} jobs")
                
                # Show sample job titles
                sample_jobs = cluster_jobs['JobProfile'].head(3).tolist()
                print(f"     Sample jobs: {', '.join(sample_jobs)}")

# =============================================================================
# VISUALIZATION
# =============================================================================

def create_clustering_visualizations(
    baseline_similarity_df: pd.DataFrame,
    enhanced_similarity_df: pd.DataFrame,
    clustering_results: Dict[str, Any],
    job_metadata: pd.DataFrame
) -> None:
    """Create visualizations comparing clustering approaches"""
    print("\n📈 Creating clustering visualizations...")
    
    # 1. Similarity distribution comparison
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    
    # Extract upper triangle values for comparison
    n = baseline_similarity_df.shape[0]
    triu_indices = np.triu_indices(n, k=1)
    
    baseline_sims = baseline_similarity_df.values[triu_indices]
    enhanced_sims = enhanced_similarity_df.values[triu_indices]
    
    axes[0].hist(baseline_sims, bins=50, alpha=0.7, label='Baseline', color='skyblue')
    axes[0].hist(enhanced_sims, bins=50, alpha=0.7, label='Enhanced', color='lightcoral')
    axes[0].set_xlabel('Job Similarity')
    axes[0].set_ylabel('Frequency')
    axes[0].set_title('Job Similarity Distribution Comparison')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # 2. Improvement distribution
    improvements = enhanced_sims - baseline_sims
    axes[1].hist(improvements, bins=50, alpha=0.7, color='lightgreen')
    axes[1].axvline(np.mean(improvements), color='red', linestyle='--', 
                    label=f'Mean: {np.mean(improvements):.4f}')
    axes[1].set_xlabel('Similarity Improvement')
    axes[1].set_ylabel('Frequency')
    axes[1].set_title('Defining Skills Similarity Improvement')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    save_plot(fig, "similarity_comparison", "Job Similarity: Baseline vs Enhanced")
    plt.show()
    
    # 3. Clustering performance comparison (if we have good results)
    dbscan_results = [(k, v) for k, v in clustering_results['enhanced'].items() if k.startswith('eps_')]
    
    if dbscan_results:
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        
        # Prepare data for comparison
        eps_values = []
        min_samples_values = []
        n_clusters_baseline = []
        n_clusters_enhanced = []
        noise_baseline = []
        noise_enhanced = []
        
        for key, enhanced_result in dbscan_results:
            baseline_result = clustering_results['baseline'][key]
            params = enhanced_result['params']
            
            eps_values.append(params['eps'])
            min_samples_values.append(params['min_samples'])
            n_clusters_baseline.append(baseline_result['n_clusters'])
            n_clusters_enhanced.append(enhanced_result['n_clusters'])
            noise_baseline.append(baseline_result['noise_points'])
            noise_enhanced.append(enhanced_result['noise_points'])
        
        # Create scatter plot
        scatter_baseline = ax.scatter(eps_values, n_clusters_baseline, 
                                    s=[100-n for n in noise_baseline], 
                                    alpha=0.6, label='Baseline', c='blue')
        scatter_enhanced = ax.scatter(eps_values, n_clusters_enhanced,
                                    s=[100-n for n in noise_enhanced],
                                    alpha=0.6, label='Enhanced', c='red')
        
        ax.set_xlabel('DBSCAN eps Parameter')
        ax.set_ylabel('Number of Clusters')
        ax.set_title('DBSCAN Clustering Performance\n(Point size = inverse noise points)')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        save_plot(fig, "dbscan_performance", "DBSCAN Clustering Performance Comparison")
        plt.show()

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main execution function for job profile clustering exploration"""
    print("🏢 JOB PROFILE CLUSTERING EXPLORATION")
    print("="*60)
    print("🎯 Clustering job profiles using enhanced skill portfolio similarity")
    print("📊 Comparing baseline vs defining skills enhanced clustering")
    print(f"⚙️ Configuration: {JobClusteringConfig.DEFINING_SKILLS_PERCENTILE}% percentile, {JobClusteringConfig.GENTLE_MULTIPLIER:.2f}x multiplier")
    print()
    
    conn = connect_database()
    
    try:
        # Load data
        job_skills_df, skill_prevalence = load_job_skill_data(conn)
        
        # Create defining skills
        job_defining_skills = create_job_defining_skills(job_skills_df, skill_prevalence)
        
        # Create similarity matrices
        baseline_similarity_df, enhanced_similarity_df, job_metadata = create_job_similarity_matrix(
            job_skills_df, job_defining_skills
        )
        
        # Perform clustering comparison
        clustering_results = perform_clustering_comparison(
            baseline_similarity_df, enhanced_similarity_df, job_metadata
        )
        
        # Analyze best clustering
        analyze_best_clustering(clustering_results, job_metadata, job_skills_df)
        
        # Create visualizations
        create_clustering_visualizations(
            baseline_similarity_df, enhanced_similarity_df, 
            clustering_results, job_metadata
        )
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save similarity matrices
        baseline_output = f"job_baseline_similarity_{timestamp}.csv"
        enhanced_output = f"job_enhanced_similarity_{timestamp}.csv"
        
        baseline_similarity_df.to_csv(baseline_output)
        enhanced_similarity_df.to_csv(enhanced_output)
        
        print(f"\n💾 Baseline similarity matrix saved: {baseline_output}")
        print(f"💾 Enhanced similarity matrix saved: {enhanced_output}")
        
        return {
            'job_skills_df': job_skills_df,
            'baseline_similarity_df': baseline_similarity_df,
            'enhanced_similarity_df': enhanced_similarity_df,
            'clustering_results': clustering_results,
            'job_metadata': job_metadata
        }
        
    finally:
        conn.close()
        print(f"\n🔒 Database connection closed")

if __name__ == "__main__":
    print("🏢 JOB PROFILE CLUSTERING EXPLORATION")
    print("="*60)
    print("🎯 Finding natural job archetypes using enhanced skill portfolio similarity")
    print("📊 Comparing baseline vs defining skills enhanced approaches")
    print()
    
    results = main()
    
    print(f"\n🎉 JOB PROFILE CLUSTERING EXPLORATION COMPLETE!")
    print(f"📁 Check generated files and plots for detailed results")
    print(f"💡 Use insights to improve job archetype understanding and career pathways") 