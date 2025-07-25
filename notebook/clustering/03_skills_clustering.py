#!/usr/bin/env python3
"""
SKILLS BUNDLE EXPLORATION
========================

Clustering skills based on co-occurrence patterns to identify natural skill bundles
for learning & development pathways and organizational design.

This complements job profile clustering by identifying skill groupings that may span
across multiple job families, revealing training opportunities and skill taxonomy insights.

Purpose:
- Find natural skill bundles that co-occur across job profiles
- Identify transferable skill packages for career transitions
- Validate and improve existing skill taxonomy
- Design L&D curricula around skill bundles
- Spot emerging skill patterns for future job design

Philosophy: Skills cluster around functional capabilities that transcend job boundaries

Usage:
    python skills_bundle_exploration.py
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
from sklearn.cluster import DBSCAN, KMeans, AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import silhouette_score, calinski_harabasz_score
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from collections import defaultdict, Counter
import networkx as nx

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

class SkillsBundleConfig:
    """Configuration for skills bundle exploration"""
    
    DATABASE_PATH = DATABASE_FILE
    
    # Filtering thresholds
    MIN_JOBS_PER_SKILL = 3        # Skills must appear in at least 3 jobs
    MIN_COOCCURRENCE = 2          # Skill pairs must co-occur at least 2 times
    MAX_PREVALENCE = 80.0         # Exclude skills in >80% of jobs (too universal)
    
    # Clustering parameters to test
    DBSCAN_PARAMS = [
        {'eps': 0.3, 'min_samples': 2},
        {'eps': 0.4, 'min_samples': 2},
        {'eps': 0.5, 'min_samples': 2},
        {'eps': 0.3, 'min_samples': 3},
        {'eps': 0.4, 'min_samples': 3},
        {'eps': 0.5, 'min_samples': 3},
    ]
    
    HIERARCHICAL_PARAMS = [
        {'n_clusters': 15, 'linkage': 'ward'},
        {'n_clusters': 20, 'linkage': 'ward'},
        {'n_clusters': 25, 'linkage': 'ward'},
        {'n_clusters': 15, 'linkage': 'complete'},
        {'n_clusters': 20, 'linkage': 'complete'},
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
        conn = sqlite3.connect(SkillsBundleConfig.DATABASE_PATH)
        print(f"✅ Connected to database: {SkillsBundleConfig.DATABASE_PATH}")
        return conn
    except sqlite3.OperationalError as e:
        raise FileNotFoundError(f"Could not connect to database: {e}")

def save_plot(fig, filename: str, title: Optional[str] = None):
    """Save plot with timestamp"""
    if title:
        fig.suptitle(title, fontsize=14, fontweight='bold')
    
    if SkillsBundleConfig.SAVE_PLOTS:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        full_filename = f"skills_bundle_{filename}_{timestamp}.png"
        fig.savefig(full_filename, dpi=SkillsBundleConfig.PLOT_DPI, bbox_inches='tight')
        print(f"   📊 Plot saved: {full_filename}")

# =============================================================================
# DATA LOADING AND PREPROCESSING
# =============================================================================

def load_skills_cooccurrence_data(conn) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load and preprocess skills co-occurrence data for clustering
    
    Returns:
        Tuple of (filtered_job_skills_df, skill_cooccurrence_matrix, skill_metadata)
    """
    print("📚 Loading skills co-occurrence data for clustering...")
    
    # Load job-skill relationships
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
        (skill_stats['job_count'] >= SkillsBundleConfig.MIN_JOBS_PER_SKILL) &
        (skill_stats['prevalence_percentage'] <= SkillsBundleConfig.MAX_PREVALENCE)
    ]['Skill_Name'].tolist()
    
    # Filter job-skills data
    filtered_job_skills = job_skills_df[
        job_skills_df['Skill_Name'].isin(filtered_skills)
    ].copy()
    
    print(f"   → Total skills: {job_skills_df['Skill_Name'].nunique():,}")
    print(f"   → Filtered skills: {len(filtered_skills):,}")
    print(f"   → Filtering criteria:")
    print(f"     • Min jobs per skill: {SkillsBundleConfig.MIN_JOBS_PER_SKILL}")
    print(f"     • Max prevalence: {SkillsBundleConfig.MAX_PREVALENCE}%")
    print(f"   → Job-skill relationships: {len(filtered_job_skills):,}")
    
    # Create skill co-occurrence matrix
    print("   → Building skill co-occurrence matrix...")
    
    # Create binary job-skill matrix
    job_skill_matrix = filtered_job_skills.pivot_table(
        index='JobProfileID',
        columns='Skill_Name', 
        values='Skill_ID',
        aggfunc='count',
        fill_value=0
    )
    job_skill_matrix = (job_skill_matrix > 0).astype(int)
    
    # Calculate co-occurrence matrix (skills x skills)
    cooccurrence_matrix = np.dot(job_skill_matrix.T.values, job_skill_matrix.values)
    
    # Convert to DataFrame
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
    print(f"   → Matrix density: {(cooccurrence_matrix > 0).sum() / (cooccurrence_matrix.size) * 100:.1f}%")
    
    return filtered_job_skills, cooccurrence_df, skill_metadata

def create_skills_similarity_matrix(cooccurrence_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create skills similarity matrix using multiple similarity measures
    
    Returns:
        Combined similarity matrix
    """
    print("🔗 Creating skills similarity matrix...")
    
    # Method 1: Jaccard similarity (intersection over union)
    skills_matrix = cooccurrence_df.values
    n_skills = len(skills_matrix)
    jaccard_matrix = np.zeros((n_skills, n_skills))
    
    for i in range(n_skills):
        for j in range(n_skills):
            if i <= j:  # Only calculate upper triangle + diagonal
                skill_i = skills_matrix[i]
                skill_j = skills_matrix[j]
                
                intersection = np.sum((skill_i > 0) & (skill_j > 0))
                union = np.sum((skill_i > 0) | (skill_j > 0))
                
                if union > 0:
                    jaccard_sim = intersection / union
                else:
                    jaccard_sim = 0.0
                
                jaccard_matrix[i, j] = jaccard_sim
                jaccard_matrix[j, i] = jaccard_sim  # Symmetric
    
    # Method 2: Cosine similarity
    cosine_matrix = cosine_similarity(skills_matrix)
    
    # Method 3: Pearson correlation
    correlation_matrix = np.corrcoef(skills_matrix)
    correlation_matrix = np.nan_to_num(correlation_matrix, nan=0.0)
    
    # Combine similarities (weighted average)
    combined_matrix = (
        0.4 * jaccard_matrix +
        0.4 * cosine_matrix + 
        0.2 * correlation_matrix
    )
    
    # Ensure diagonal is 1.0
    np.fill_diagonal(combined_matrix, 1.0)
    
    # Convert to DataFrame
    similarity_df = pd.DataFrame(
        combined_matrix,
        index=cooccurrence_df.index,
        columns=cooccurrence_df.columns
    )
    
    print(f"   → Similarity matrix created using combined Jaccard, Cosine, and Correlation")
    print(f"   → Mean similarity: {np.mean(combined_matrix[np.triu_indices_from(combined_matrix, k=1)]):.3f}")
    print(f"   → Max similarity: {np.max(combined_matrix[np.triu_indices_from(combined_matrix, k=1)]):.3f}")
    
    return similarity_df

# =============================================================================
# CLUSTERING ANALYSIS
# =============================================================================

def perform_skills_clustering(
    similarity_df: pd.DataFrame,
    skill_metadata: pd.DataFrame
) -> Dict[str, Any]:
    """
    Perform multiple clustering approaches on skills
    
    Returns:
        Dict with clustering results and evaluation metrics
    """
    print("\n🔍 PERFORMING SKILLS CLUSTERING")
    print("="*50)
    
    # Convert similarity to distance for clustering
    distance_matrix = 1 - similarity_df.values
    distance_matrix = np.maximum(distance_matrix, 0)  # Ensure non-negative
    
    clustering_results = {
        'dbscan': {},
        'hierarchical': {},
        'evaluation': {}
    }
    
    # Test DBSCAN parameters
    print("\n📊 Testing DBSCAN Parameters:")
    print("-" * 40)
    
    best_dbscan_score = -1
    best_dbscan_key = None
    
    for params in SkillsBundleConfig.DBSCAN_PARAMS:
        eps = params['eps']
        min_samples = params['min_samples']
        
        print(f"\n🔧 DBSCAN: eps={eps}, min_samples={min_samples}")
        
        # Perform clustering
        dbscan = DBSCAN(eps=eps, min_samples=min_samples, metric='precomputed')
        labels = dbscan.fit_predict(distance_matrix)
        
        # Calculate metrics
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        noise_points = list(labels).count(-1)
        
        print(f"   → Clusters: {n_clusters}, Noise points: {noise_points}")
        
        # Calculate silhouette score if we have clusters
        silhouette = None
        if n_clusters > 1 and noise_points < len(labels):
            try:
                # Only use non-noise points for silhouette calculation
                non_noise_mask = labels != -1
                if np.sum(non_noise_mask) > 1:
                    silhouette = silhouette_score(
                        distance_matrix[non_noise_mask][:, non_noise_mask],
                        labels[non_noise_mask],
                        metric='precomputed'
                    )
                    print(f"   → Silhouette score: {silhouette:.3f}")
                    
                    # Update best score
                    if silhouette > best_dbscan_score:
                        best_dbscan_score = silhouette
                        best_dbscan_key = f"eps_{eps}_min_{min_samples}"
            except:
                print(f"   → Could not calculate silhouette score")
        
        # Store results
        param_key = f"eps_{eps}_min_{min_samples}"
        clustering_results['dbscan'][param_key] = {
            'labels': labels,
            'n_clusters': n_clusters,
            'noise_points': noise_points,
            'silhouette_score': silhouette,
            'params': params
        }
    
    # Test Hierarchical clustering parameters
    print(f"\n📊 Testing Hierarchical Clustering Parameters:")
    print("-" * 40)
    
    best_hierarchical_score = -1
    best_hierarchical_key = None
    
    for params in SkillsBundleConfig.HIERARCHICAL_PARAMS:
        n_clusters = params['n_clusters']
        linkage = params['linkage']
        
        print(f"\n🔧 Hierarchical: n_clusters={n_clusters}, linkage={linkage}")
        
        # Perform clustering
        hierarchical = AgglomerativeClustering(
            n_clusters=n_clusters,
            linkage=linkage,
            metric='precomputed' if linkage != 'ward' else 'euclidean'
        )
        
        if linkage == 'ward':
            # Ward requires euclidean distance, use similarity matrix directly
            labels = hierarchical.fit_predict(similarity_df.values)
        else:
            labels = hierarchical.fit_predict(distance_matrix)
        
        # Calculate silhouette score
        try:
            if linkage == 'ward':
                silhouette = silhouette_score(similarity_df.values, labels)
            else:
                silhouette = silhouette_score(distance_matrix, labels, metric='precomputed')
            print(f"   → Silhouette score: {silhouette:.3f}")
            
            # Update best score
            if silhouette > best_hierarchical_score:
                best_hierarchical_score = silhouette
                best_hierarchical_key = f"n_{n_clusters}_{linkage}"
                
        except Exception as e:
            silhouette = None
            print(f"   → Could not calculate silhouette score: {e}")
        
        # Store results
        param_key = f"n_{n_clusters}_{linkage}"
        clustering_results['hierarchical'][param_key] = {
            'labels': labels,
            'n_clusters': n_clusters,
            'silhouette_score': silhouette,
            'params': params
        }
    
    # Store best results
    clustering_results['evaluation'] = {
        'best_dbscan': best_dbscan_key,
        'best_dbscan_score': best_dbscan_score,
        'best_hierarchical': best_hierarchical_key,
        'best_hierarchical_score': best_hierarchical_score
    }
    
    return clustering_results

def analyze_skill_bundles(
    clustering_results: Dict[str, Any],
    skill_metadata: pd.DataFrame,
    similarity_df: pd.DataFrame
) -> None:
    """Analyze the best clustering results to understand skill bundles"""
    print("\n🏆 SKILL BUNDLE ANALYSIS")
    print("="*50)
    
    # Get best clustering result
    eval_results = clustering_results['evaluation']
    
    if eval_results['best_hierarchical_score'] > eval_results['best_dbscan_score']:
        best_method = 'hierarchical'
        best_key = eval_results['best_hierarchical']
        best_result = clustering_results['hierarchical'][best_key]
    else:
        best_method = 'dbscan'
        best_key = eval_results['best_dbscan'] 
        best_result = clustering_results['dbscan'][best_key]
    
    print(f"🥇 Best Clustering: {best_method.upper()} - {best_key}")
    print(f"   → Silhouette score: {best_result['silhouette_score']:.3f}")
    print(f"   → Parameters: {best_result['params']}")
    
    labels = best_result['labels']
    skill_names = similarity_df.index.tolist()
    
    # Create analysis DataFrame
    analysis_df = skill_metadata.copy()
    analysis_df['skill_bundle'] = labels
    
    # Analyze bundles
    unique_bundles = sorted(set(labels))
    
    print(f"\n📊 Skill Bundle Analysis:")
    
    for bundle_id in unique_bundles:
        if bundle_id == -1:
            continue  # Skip noise points for now
        
        bundle_skills = analysis_df[analysis_df['skill_bundle'] == bundle_id]
        
        print(f"\n🔹 Bundle {bundle_id} ({len(bundle_skills)} skills):")
        
        # Category distribution
        category_counts = bundle_skills['Skill_Category'].value_counts()
        print(f"   📂 Categories: {', '.join([f'{cat}({count})' for cat, count in category_counts.head(3).items()])}")
        
        # Skill type distribution
        type_counts = bundle_skills['SkillType'].value_counts()
        print(f"   🏷️ Types: {', '.join([f'{typ}({count})' for typ, count in type_counts.head(2).items()])}")
        
        # Average prevalence
        avg_prevalence = bundle_skills['prevalence_percentage'].mean()
        print(f"   📈 Avg prevalence: {avg_prevalence:.1f}%")
        
        # Sample skills (most and least prevalent)
        bundle_skills_sorted = bundle_skills.sort_values('prevalence_percentage', ascending=False)
        top_skills = bundle_skills_sorted.head(3).index.tolist()
        bottom_skills = bundle_skills_sorted.tail(2).index.tolist()
        
        print(f"   🏆 Representative skills: {', '.join(top_skills)}")
        print(f"   💎 Specialized skills: {', '.join(bottom_skills)}")
        
        # Internal bundle similarity
        bundle_skill_names = bundle_skills.index.tolist()
        if len(bundle_skill_names) > 1:
            bundle_similarity_matrix = similarity_df.loc[bundle_skill_names, bundle_skill_names]
            avg_internal_similarity = np.mean(bundle_similarity_matrix.values[np.triu_indices_from(bundle_similarity_matrix.values, k=1)])
            print(f"   🔗 Internal similarity: {avg_internal_similarity:.3f}")
    
    # Handle noise points if DBSCAN was used
    if best_method == 'dbscan' and -1 in labels:
        noise_skills = analysis_df[analysis_df['skill_bundle'] == -1]
        print(f"\n🔸 Noise Points ({len(noise_skills)} skills):")
        print(f"   → These skills don't cluster well with others")
        
        # Show categories of noise skills
        noise_categories = noise_skills['Skill_Category'].value_counts().head(5)
        print(f"   📂 Top categories: {', '.join([f'{cat}({count})' for cat, count in noise_categories.items()])}")
        
        # Show some examples
        sample_noise = noise_skills.sample(min(5, len(noise_skills))).index.tolist()
        print(f"   🔍 Examples: {', '.join(sample_noise)}")

def create_taxonomy_validation_overlay(
    clustering_results: Dict[str, Any],
    skill_metadata: pd.DataFrame,
    similarity_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Create taxonomy validation overlay comparing clustering results with existing categories
    
    Returns:
        DataFrame with validation insights
    """
    print("\n🔍 TAXONOMY VALIDATION OVERLAY")
    print("="*50)
    
    # Get best clustering result
    eval_results = clustering_results['evaluation']
    
    if eval_results['best_hierarchical_score'] > eval_results['best_dbscan_score']:
        best_result = clustering_results['hierarchical'][eval_results['best_hierarchical']]
    else:
        best_result = clustering_results['dbscan'][eval_results['best_dbscan']]
    
    labels = best_result['labels']
    
    # Create validation DataFrame
    validation_df = skill_metadata.copy()
    validation_df['discovered_bundle'] = labels
    validation_df['skill_name'] = validation_df.index
    
    # Compare existing categories with discovered bundles
    print("📊 Category vs Bundle Alignment Analysis:")
    
    category_bundle_crosstab = pd.crosstab(
        validation_df['Skill_Category'],
        validation_df['discovered_bundle'],
        margins=True
    )
    
    print(f"\n🏷️ Cross-tabulation: Existing Categories vs Discovered Bundles")
    print(category_bundle_crosstab)
    
    # Find misaligned skills (skills in different bundles than their category peers)
    misalignment_insights = []
    
    for category in validation_df['Skill_Category'].unique():
        category_skills = validation_df[validation_df['Skill_Category'] == category]
        bundle_distribution = category_skills['discovered_bundle'].value_counts()
        
        # If category skills are spread across multiple bundles, investigate
        if len(bundle_distribution) > 1:
            dominant_bundle = bundle_distribution.index[0]
            outlier_skills = category_skills[category_skills['discovered_bundle'] != dominant_bundle]
            
            for _, skill_row in outlier_skills.iterrows():
                misalignment_insights.append({
                    'skill_name': skill_row['skill_name'],
                    'existing_category': category,
                    'discovered_bundle': skill_row['discovered_bundle'], 
                    'category_dominant_bundle': dominant_bundle,
                    'prevalence': skill_row['prevalence_percentage']
                })
    
    # Convert to DataFrame
    misalignment_df = pd.DataFrame(misalignment_insights)
    
    if len(misalignment_df) > 0:
        print(f"\n🔍 Potential Taxonomy Misalignments ({len(misalignment_df)} skills):")
        print("   → Skills that cluster differently than their assigned category:")
        
        for _, row in misalignment_df.head(10).iterrows():
            print(f"   • {row['skill_name']} (Category: {row['existing_category']}, "
                  f"Bundle: {row['discovered_bundle']}, Prevalence: {row['prevalence']:.1f}%)")
    
    # Find highly similar skills across different categories
    print(f"\n🔗 Cross-Category Skill Similarities:")
    
    cross_category_similarities = []
    skill_names = similarity_df.index.tolist()
    
    for i, skill_a in enumerate(skill_names):
        for j, skill_b in enumerate(skill_names):
            if i < j:  # Avoid duplicates
                category_a = validation_df.loc[skill_a, 'Skill_Category']
                category_b = validation_df.loc[skill_b, 'Skill_Category']
                
                # Only look at skills from different categories
                if category_a != category_b:
                    similarity = similarity_df.loc[skill_a, skill_b]
                    
                    if similarity > 0.7:  # High similarity threshold
                        cross_category_similarities.append({
                            'skill_a': skill_a,
                            'skill_b': skill_b,
                            'similarity': similarity,
                            'category_a': category_a,
                            'category_b': category_b
                        })
    
    # Sort by similarity and show top findings
    cross_category_similarities.sort(key=lambda x: x['similarity'], reverse=True)
    
    print("   → Highly similar skills from different categories:")
    for insight in cross_category_similarities[:10]:
        print(f"   • {insight['skill_a']} ({insight['category_a']}) ↔ "
              f"{insight['skill_b']} ({insight['category_b']}) | "
              f"Similarity: {insight['similarity']:.3f}")
    
    return validation_df

# =============================================================================
# VISUALIZATION
# =============================================================================

def create_skills_bundle_visualizations(
    clustering_results: Dict[str, Any],
    skill_metadata: pd.DataFrame,
    similarity_df: pd.DataFrame
) -> None:
    """Create visualizations for skills bundle analysis"""
    print("\n📈 Creating skills bundle visualizations...")
    
    # Get best clustering result
    eval_results = clustering_results['evaluation']
    
    if eval_results['best_hierarchical_score'] > eval_results['best_dbscan_score']:
        best_result = clustering_results['hierarchical'][eval_results['best_hierarchical']]
        method_name = "Hierarchical"
    else:
        best_result = clustering_results['dbscan'][eval_results['best_dbscan']]
        method_name = "DBSCAN"
    
    labels = best_result['labels']
    
    # 1. Bundle size distribution
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # Bundle sizes
    bundle_sizes = pd.Series(labels).value_counts().sort_index()
    if -1 in bundle_sizes.index:
        bundle_sizes = bundle_sizes.drop(-1)  # Remove noise points
    
    axes[0, 0].bar(range(len(bundle_sizes)), bundle_sizes.values, alpha=0.7, color='skyblue')
    axes[0, 0].set_xlabel('Skill Bundle ID')
    axes[0, 0].set_ylabel('Number of Skills')
    axes[0, 0].set_title(f'Skill Bundle Sizes ({method_name} Clustering)')
    axes[0, 0].grid(True, alpha=0.3)
    
    # Bundle prevalence distribution
    analysis_df = skill_metadata.copy()
    analysis_df['skill_bundle'] = labels
    
    bundle_prevalences = []
    for bundle_id in bundle_sizes.index:
        bundle_skills = analysis_df[analysis_df['skill_bundle'] == bundle_id]
        avg_prevalence = bundle_skills['prevalence_percentage'].mean()
        bundle_prevalences.append(avg_prevalence)
    
    axes[0, 1].bar(range(len(bundle_prevalences)), bundle_prevalences, alpha=0.7, color='lightcoral')
    axes[0, 1].set_xlabel('Skill Bundle ID')
    axes[0, 1].set_ylabel('Average Skill Prevalence (%)')
    axes[0, 1].set_title('Average Skill Prevalence by Bundle')
    axes[0, 1].grid(True, alpha=0.3)
    
    # Category distribution across bundles
    category_bundle_counts = pd.crosstab(analysis_df['Skill_Category'], analysis_df['skill_bundle'])
    if -1 in category_bundle_counts.columns:
        category_bundle_counts = category_bundle_counts.drop(-1, axis=1)
    
    # Show top categories
    top_categories = category_bundle_counts.sum(axis=1).nlargest(8).index
    category_subset = category_bundle_counts.loc[top_categories]
    
    im = axes[1, 0].imshow(category_subset.values, cmap='Blues', aspect='auto')
    axes[1, 0].set_xticks(range(len(category_subset.columns)))
    axes[1, 0].set_xticklabels(category_subset.columns)
    axes[1, 0].set_yticks(range(len(category_subset.index)))
    axes[1, 0].set_yticklabels(category_subset.index, fontsize=8)
    axes[1, 0].set_xlabel('Skill Bundle ID')
    axes[1, 0].set_title('Category Distribution Across Bundles')
    plt.colorbar(im, ax=axes[1, 0])
    
    # Silhouette score comparison
    methods = []
    scores = []
    
    for method, results in clustering_results.items():
        if method == 'evaluation':
            continue
        for key, result in results.items():
            if result['silhouette_score'] is not None:
                methods.append(f"{method}_{key}")
                scores.append(result['silhouette_score'])
    
    # Sort by score
    sorted_data = sorted(zip(methods, scores), key=lambda x: x[1], reverse=True)
    methods, scores = zip(*sorted_data)
    
    # Take top 10 for readability
    if len(methods) > 10:
        methods = methods[:10]
        scores = scores[:10]
    
    axes[1, 1].barh(range(len(scores)), scores, alpha=0.7, color='lightgreen')
    axes[1, 1].set_yticks(range(len(methods)))
    axes[1, 1].set_yticklabels([m.replace('_', '\n') for m in methods], fontsize=8)
    axes[1, 1].set_xlabel('Silhouette Score')
    axes[1, 1].set_title('Clustering Performance Comparison')
    axes[1, 1].grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    save_plot(fig, "bundle_analysis", "Skills Bundle Analysis")
    plt.show()

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main execution function for skills bundle exploration"""
    print("🎯 SKILLS BUNDLE EXPLORATION")
    print("="*60)
    print("🔍 Discovering natural skill bundles for L&D pathways and org design")
    print("📊 Complementing job profile clustering with skill grouping insights")
    print("🔧 Validating and improving existing skill taxonomy")
    print()
    
    conn = connect_database()
    
    try:
        # Load and preprocess data
        job_skills_df, cooccurrence_df, skill_metadata = load_skills_cooccurrence_data(conn)
        
        # Create similarity matrix
        similarity_df = create_skills_similarity_matrix(cooccurrence_df)
        
        # Perform clustering
        clustering_results = perform_skills_clustering(similarity_df, skill_metadata)
        
        # Analyze skill bundles
        analyze_skill_bundles(clustering_results, skill_metadata, similarity_df)
        
        # Create taxonomy validation overlay
        validation_df = create_taxonomy_validation_overlay(
            clustering_results, skill_metadata, similarity_df
        )
        
        # Create visualizations
        create_skills_bundle_visualizations(
            clustering_results, skill_metadata, similarity_df
        )
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save skill bundles
        eval_results = clustering_results['evaluation']
        if eval_results['best_hierarchical_score'] > eval_results['best_dbscan_score']:
            best_result = clustering_results['hierarchical'][eval_results['best_hierarchical']]
        else:
            best_result = clustering_results['dbscan'][eval_results['best_dbscan']]
        
        skill_bundles_df = skill_metadata.copy()
        skill_bundles_df['skill_bundle'] = best_result['labels']
        skill_bundles_df['skill_name'] = skill_bundles_df.index
        
        bundles_output = f"skill_bundles_{timestamp}.csv"
        skill_bundles_df.to_csv(bundles_output, index=False)
        print(f"\n💾 Skill bundles saved: {bundles_output}")
        
        # Save validation insights
        validation_output = f"taxonomy_validation_{timestamp}.csv"
        validation_df.to_csv(validation_output, index=False)
        print(f"💾 Taxonomy validation saved: {validation_output}")
        
        # Save similarity matrix
        similarity_output = f"skills_similarity_matrix_{timestamp}.csv"
        similarity_df.to_csv(similarity_output)
        print(f"💾 Skills similarity matrix saved: {similarity_output}")
        
        return {
            'skill_bundles_df': skill_bundles_df,
            'validation_df': validation_df,
            'similarity_df': similarity_df,
            'clustering_results': clustering_results
        }
        
    finally:
        conn.close()
        print(f"\n🔒 Database connection closed")

if __name__ == "__main__":
    print("🎯 SKILLS BUNDLE EXPLORATION")
    print("="*60)
    print("🔍 Discovering natural skill bundles that transcend job boundaries")
    print("📚 Supporting L&D curriculum design and organizational capability mapping")
    print()
    
    results = main()
    
    print(f"\n🎉 SKILLS BUNDLE EXPLORATION COMPLETE!")
    print(f"📁 Check generated files and plots for detailed insights")
    print(f"💡 Use skill bundles to design training pathways and validate taxonomy") 