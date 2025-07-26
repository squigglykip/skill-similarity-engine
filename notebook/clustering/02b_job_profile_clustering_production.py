#!/usr/bin/env python3
"""
JOB PROFILE CLUSTERING - PRODUCTION
===================================

Production-ready job profile clustering using optimal parameters discovered through
comprehensive parameter optimization. Generates 331 job clusters with 0.962 silhouette
score using enhanced similarity with defining skills strategy.

Purpose:
- Generate production job profile clusters for strategic use
- Implement optimal DBSCAN parameters (eps=0.1, min_samples=2)
- Apply enhanced similarity with defining skills (20% percentile + 1.05x multiplier)
- Create job archetype characterization and analysis
- Output cluster assignments and strategic intelligence reports

Philosophy: Production clustering for immediate strategic value

Usage:
    python 02b_job_profile_clustering_production.py
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
from sklearn.cluster import DBSCAN
from sklearn.metrics import silhouette_score, silhouette_samples
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

class JobClusteringProductionConfig:
    """Configuration for production job profile clustering"""
    
    DATABASE_PATH = DATABASE_FILE
    
    # Optimal parameters from parameter optimization (hardcoded)
    OPTIMAL_DBSCAN_PARAMS = {
        'eps': 0.1,
        'min_samples': 2
    }
    
    # Enhanced similarity configuration (empirically validated)
    DEFINING_SKILLS_PERCENTILE = 20   # Top 20% rarest skills per job profile
    GENTLE_MULTIPLIER = 1.05          # 5% boost per shared defining skill
    
    # Expected results (from optimization)
    EXPECTED_CLUSTERS = 331
    EXPECTED_SILHOUETTE = 0.962
    EXPECTED_NOISE_RATIO = 0.052
    
    # Output settings
    SAVE_PLOTS = True
    PLOT_DPI = 300
    FIGURE_SIZE = (14, 10)
    
    # Analysis settings
    TOP_SKILLS_PER_CLUSTER = 10      # Top skills to show per cluster
    MIN_CLUSTER_SIZE_ANALYSIS = 3    # Minimum cluster size for detailed analysis

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def connect_database():
    """Connect to the workforce intelligence database"""
    try:
        conn = sqlite3.connect(JobClusteringProductionConfig.DATABASE_PATH)
        print(f"✅ Connected to database: {JobClusteringProductionConfig.DATABASE_PATH}")
        return conn
    except sqlite3.OperationalError as e:
        raise FileNotFoundError(f"Could not connect to database: {e}")

def save_plot(fig, filename: str, title: Optional[str] = None):
    """Save plot with timestamp and title"""
    if title:
        fig.suptitle(title, fontsize=16, fontweight='bold')
    
    if JobClusteringProductionConfig.SAVE_PLOTS:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        full_filename = f"job_clusters_production_{filename}_{timestamp}.png"
        fig.savefig(full_filename, dpi=JobClusteringProductionConfig.PLOT_DPI, bbox_inches='tight')
        print(f"   📊 Plot saved: {full_filename}")

def create_timestamp():
    """Create timestamp for output files"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

# =============================================================================
# DATA LOADING AND PROCESSING
# =============================================================================

def load_job_skill_data(conn) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load comprehensive job-skill data for clustering
    
    Returns:
        Tuple of (job_skills_df, job_metadata_df)
    """
    print("📚 Loading comprehensive job-skill data...")
    
    # Load job-skill relationships with full context
    job_skills_query = """
    SELECT 
        js.JobProfileID,
        js.Skill_ID,
        s.Skill_Name,
        s.Category as Skill_Category,
        j.JobProfile,
        j.JobFunction,
        j.JobSubFunction,
        j.JobCategory,
        j.ManagementLevel
    FROM job_skills js
    JOIN skills s ON js.Skill_ID = s.Skill_ID
    JOIN jobs j ON js.JobProfileID = j.JobProfileID
    WHERE js.JobProfileID IS NOT NULL 
      AND s.Skill_Name IS NOT NULL
    ORDER BY js.JobProfileID, s.Skill_Name
    """
    
    job_skills_df = pd.read_sql_query(job_skills_query, conn)
    
    print(f"   → Loaded columns: {list(job_skills_df.columns)}")
    
    # Create job metadata using core taxonomy fields
    core_columns = ['JobProfileID', 'JobProfile', 'JobFunction', 'JobSubFunction', 
                   'JobCategory', 'ManagementLevel']
    
    job_metadata_df = job_skills_df[core_columns].drop_duplicates()
    
    print(f"   → Job-skill relationships: {len(job_skills_df):,}")
    print(f"   → Unique job profiles: {job_metadata_df['JobProfileID'].nunique():,}")
    print(f"   → Unique skills: {job_skills_df['Skill_Name'].nunique():,}")
    
    return job_skills_df, job_metadata_df

def calculate_defining_skills(job_skills_df: pd.DataFrame) -> Dict[int, Set[str]]:
    """
    Calculate defining skills for each job profile using 20% percentile strategy
    
    Returns:
        Dictionary mapping JobProfileID to set of defining skills
    """
    print("🎯 Calculating defining skills (20% percentile strategy)...")
    
    # Calculate skill rarity (inverse of prevalence)
    skill_counts = job_skills_df['Skill_Name'].value_counts()
    total_jobs = job_skills_df['JobProfileID'].nunique()
    skill_rarity = (total_jobs - skill_counts) / total_jobs
    
    job_defining_skills = {}
    
    for job_id, job_group in job_skills_df.groupby('JobProfileID'):
        job_skills = job_group['Skill_Name'].tolist()
        
        # Get rarity scores for this job's skills
        skill_rarities = [skill_rarity.get(skill, 0) for skill in job_skills]
        
        if skill_rarities:
            # Calculate 20% percentile threshold
            rarity_threshold = np.percentile(skill_rarities, 100 - JobClusteringProductionConfig.DEFINING_SKILLS_PERCENTILE)
            
            # Select skills above threshold
            defining_skills = set()
            for skill, rarity in zip(job_skills, skill_rarities):
                if rarity >= rarity_threshold:
                    defining_skills.add(skill)
            
            job_defining_skills[job_id] = defining_skills
        else:
            job_defining_skills[job_id] = set()
    
    avg_defining_skills = np.mean([len(skills) for skills in job_defining_skills.values()])
    print(f"   → Average defining skills per job: {avg_defining_skills:.1f}")
    print(f"   → Defining skills percentile: {JobClusteringProductionConfig.DEFINING_SKILLS_PERCENTILE}%")
    
    return job_defining_skills

def create_enhanced_similarity_matrix(
    job_skills_df: pd.DataFrame, 
    job_defining_skills: Dict[int, Set[str]]
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Create enhanced similarity matrix using defining skills strategy
    
    Returns:
        Tuple of (enhanced_similarity_df, job_metadata_df)
    """
    print("🔗 Creating enhanced similarity matrix with defining skills...")
    
    # Get job metadata and create job-to-skills mapping
    job_metadata = job_skills_df[['JobProfileID', 'JobProfile', 'JobFunction', 
                                 'JobSubFunction', 'JobCategory', 'ManagementLevel']].drop_duplicates()
    job_ids = job_metadata['JobProfileID'].tolist()
    
    job_to_skills = {}
    for job_id, job_group in job_skills_df.groupby('JobProfileID'):
        job_to_skills[job_id] = set(job_group['Skill_Name'])
    
    print(f"   → Calculating similarities for {len(job_ids):,} job profiles...")
    
    n_jobs = len(job_ids)
    enhanced_matrix = np.zeros((n_jobs, n_jobs))
    
    # Calculate enhanced similarity matrix
    for i, job_a in enumerate(job_ids):
        if i % 100 == 0:
            print(f"   → Progress: {i}/{n_jobs} ({i/n_jobs*100:.1f}%)")
            
        for j, job_b in enumerate(job_ids):
            if i <= j:
                job_a_skills = job_to_skills[job_a]
                job_b_skills = job_to_skills[job_b]
                
                if job_a_skills and job_b_skills:
                    # Calculate baseline Jaccard similarity
                    shared_skills = job_a_skills & job_b_skills
                    total_skills = job_a_skills | job_b_skills
                    baseline_sim = len(shared_skills) / len(total_skills)
                else:
                    baseline_sim = 0.0
                
                if i == j:
                    enhanced_sim = 1.0
                else:
                    # Apply defining skills enhancement
                    job_a_defining = job_defining_skills.get(job_a, set())
                    job_b_defining = job_defining_skills.get(job_b, set())
                    all_defining = job_a_defining | job_b_defining
                    
                    shared_defining = [skill for skill in (job_a_skills & job_b_skills) if skill in all_defining]
                    
                    # Apply gentle multiplier
                    defining_skill_boost = len(shared_defining) * (JobClusteringProductionConfig.GENTLE_MULTIPLIER - 1.0)
                    enhanced_sim = baseline_sim * (1.0 + defining_skill_boost)
                    enhanced_sim = min(1.0, enhanced_sim)
                
                enhanced_matrix[i, j] = enhanced_sim
                enhanced_matrix[j, i] = enhanced_sim
    
    enhanced_similarity_df = pd.DataFrame(enhanced_matrix, index=job_ids, columns=job_ids)
    
    print(f"   → Enhanced similarity matrix created: {enhanced_similarity_df.shape}")
    
    return enhanced_similarity_df, job_metadata

# =============================================================================
# CLUSTER NAMING FUNCTIONS
# =============================================================================

def analyze_management_level_pattern(cluster_jobs: pd.DataFrame) -> str:
    """Analyze management level patterns in cluster"""
    if len(cluster_jobs) == 0:
        return "Mixed"
    
    # Map management levels to numerical values for analysis
    level_mapping = {
        'Group 1': 1, 'Group 2': 2, 'Group 3': 3, 'Group 4': 4,
        'Group 5': 5, 'Group 6': 6, 'Group 7': 7, 'Group NA': 0
    }
    
    cluster_jobs['Level_Numeric'] = cluster_jobs['ManagementLevel'].map(level_mapping).fillna(0)
    avg_level = cluster_jobs['Level_Numeric'].mean()
    
    if avg_level >= 5:
        return "Leadership"
    elif avg_level >= 3:
        return "Specialists"
    elif avg_level >= 1:
        return "Associate"
    else:
        return "Mixed"

def get_dominant_category(cluster_data: pd.DataFrame, column: str, threshold: float = 0.6) -> Optional[str]:
    """Get dominant category if it exceeds threshold"""
    if len(cluster_data) == 0:
        return None
    
    value_counts = cluster_data[column].value_counts()
    if len(value_counts) == 0:
        return None
    
    most_common = value_counts.iloc[0]
    total = len(cluster_data)
    
    if most_common / total >= threshold:
        return str(value_counts.index[0])
    return None

def calculate_ratio(cluster_data: pd.DataFrame, column: str, target_value: str) -> float:
    """Calculate ratio of specific value in column"""
    if len(cluster_data) == 0:
        return 0.0
    
    # Check if column exists
    if column not in cluster_data.columns:
        print(f"   Warning: Column '{column}' not found. Available columns: {list(cluster_data.columns)}")
        return 0.0
    
    return (cluster_data[column] == target_value).sum() / len(cluster_data)

def analyze_functional_composition(cluster_jobs: pd.DataFrame) -> Dict[str, Any]:
    """Analyze the functional composition of a cluster in human terms"""
    if len(cluster_jobs) == 0:
        return {'dominance': 'empty', 'diversity': 'none', 'primary_function': None, 'secondary_function': None}
    
    function_counts = cluster_jobs['JobFunction'].value_counts()
    total_jobs = len(cluster_jobs)
    
    # Calculate dominance in human terms
    if len(function_counts) == 1:
        dominance = 'exclusively'
        diversity = 'uniform'
    elif function_counts.iloc[0] / total_jobs >= 0.8:
        dominance = 'predominantly'
        diversity = 'focused'
    elif function_counts.iloc[0] / total_jobs >= 0.6:
        dominance = 'primarily'
        diversity = 'concentrated'
    elif function_counts.iloc[0] / total_jobs >= 0.4:
        dominance = 'largely'
        diversity = 'mixed'
    else:
        dominance = 'diversely'
        diversity = 'varied'
    
    primary_function = function_counts.index[0] if len(function_counts) > 0 else None
    secondary_function = function_counts.index[1] if len(function_counts) > 1 else None
    
    return {
        'dominance': dominance,
        'diversity': diversity,
        'primary_function': primary_function,
        'secondary_function': secondary_function,
        'function_count': len(function_counts)
    }

def analyze_specialization_depth(cluster_jobs: pd.DataFrame) -> Dict[str, Any]:
    """Analyze how specialized vs general the cluster is"""
    if len(cluster_jobs) == 0:
        return {'specialization': 'undefined', 'focus_area': None}
    
    subfunc_counts = cluster_jobs['JobSubFunction'].value_counts()
    total_jobs = len(cluster_jobs)
    
    if len(subfunc_counts) == 1:
        specialization = 'highly specialized'
        focus_area = subfunc_counts.index[0]
    elif subfunc_counts.iloc[0] / total_jobs >= 0.7:
        specialization = 'specialized'
        focus_area = subfunc_counts.index[0]
    elif subfunc_counts.iloc[0] / total_jobs >= 0.5:
        specialization = 'moderately specialized'
        focus_area = subfunc_counts.index[0]
    else:
        specialization = 'broadly skilled'
        focus_area = None
    
    return {
        'specialization': specialization,
        'focus_area': focus_area
    }

def create_professional_description(composition: Dict, specialization: Dict, level_pattern: str, cluster_size: int) -> str:
    """Create a professional, human-readable description"""
    
    # Start with the functional composition
    if composition['primary_function']:
        if composition['dominance'] == 'exclusively':
            base_desc = f"entirely focused on {composition['primary_function']}"
        elif composition['dominance'] == 'predominantly':
            base_desc = f"centered around {composition['primary_function']} with minimal functional diversity"
        elif composition['dominance'] == 'primarily':
            base_desc = f"concentrated in {composition['primary_function']} while including related functions"
        elif composition['dominance'] == 'largely':
            base_desc = f"spanning {composition['primary_function']} and complementary areas"
        else:
            base_desc = f"encompassing diverse functions including {composition['primary_function']}"
    else:
        base_desc = "representing multiple functional areas"
    
    # Add specialization context
    if specialization['focus_area'] and specialization['specialization'] in ['highly specialized', 'specialized']:
        if specialization['focus_area'] != composition['primary_function']:
            focus_short = specialization['focus_area'][:30] + "..." if len(specialization['focus_area']) > 30 else specialization['focus_area']
            base_desc += f", {specialization['specialization']} in {focus_short}"
    
    # Add level context
    if level_pattern == "Leadership":
        base_desc += ", operating at senior management and leadership levels"
    elif level_pattern == "Specialists":
        base_desc += ", comprising experienced specialists and subject matter experts"
    elif level_pattern == "Associate":
        base_desc += ", consisting of early-career and developing professionals"
    
    return base_desc

def generate_job_cluster_name(cluster_jobs: pd.DataFrame, cluster_id: int) -> Dict[str, str]:
    """
    Generate structured, human-readable names for job clusters
    
    Returns:
        Dict with 'cluster_name', 'cluster_title', 'cluster_description', 'confidence', and 'naming_rationale'
    """
    if len(cluster_jobs) == 0:
        return {
            'cluster_name': f"Empty Cluster {cluster_id}",
            'cluster_title': "Empty Cluster",
            'cluster_description': "No jobs assigned to this cluster",
            'confidence': 'Low',
            'naming_rationale': 'No jobs in cluster'
        }
    
    # Analyze cluster composition
    composition = analyze_functional_composition(cluster_jobs)
    specialization = analyze_specialization_depth(cluster_jobs)
    level_pattern = analyze_management_level_pattern(cluster_jobs)
    
    # Create structured naming
    cluster_size = len(cluster_jobs)
    
    # TITLE: Concise, professional identifier
    if composition['primary_function']:
        if level_pattern != "Mixed":
            title = f"{composition['primary_function']} {level_pattern}"
        else:
            title = f"{composition['primary_function']} Professionals"
    else:
        if level_pattern != "Mixed":
            title = f"Cross-Functional {level_pattern}"
        else:
            title = "Multi-Functional Professionals"
    
    # SUBTITLE: Adds specialization context if relevant
    subtitle = ""
    if specialization['focus_area'] and specialization['focus_area'] != composition['primary_function']:
        if specialization['specialization'] in ['highly specialized', 'specialized']:
            focus_short = specialization['focus_area'][:25] + "..." if len(specialization['focus_area']) > 25 else specialization['focus_area']
            subtitle = f"Specializing in {focus_short}"
    
    # DESCRIPTION: Full professional description
    description = create_professional_description(composition, specialization, level_pattern, cluster_size)
    
    # COMBINED NAME: Title + Subtitle for primary display
    if subtitle:
        cluster_name = f"{title} - {subtitle}"
    else:
        cluster_name = title
    
    # Confidence assessment
    confidence = "High"
    rationale_parts = []
    
    if composition['dominance'] in ['exclusively', 'predominantly', 'primarily']:
        rationale_parts.append(f"strong functional coherence ({composition['dominance']} {composition['primary_function']})")
    else:
        confidence = "Medium"
        rationale_parts.append(f"moderate functional diversity ({composition['dominance']} represented)")
    
    if cluster_size < 3:
        confidence = "Low"
        rationale_parts.append("limited cluster size")
    elif cluster_size >= 8:
        rationale_parts.append("substantial cluster size")
    
    if level_pattern != "Mixed":
        rationale_parts.append(f"clear {level_pattern.lower()} level pattern")
    
    # Ensure names aren't too long for display
    if len(cluster_name) > 65:
        cluster_name = cluster_name[:62] + "..."
    
    return {
        'cluster_name': cluster_name,
        'cluster_title': title,
        'cluster_description': description,
        'confidence': confidence,
        'naming_rationale': '; '.join(rationale_parts)
    }

# =============================================================================
# CLUSTERING FUNCTIONS
# =============================================================================

def perform_production_clustering(similarity_df: pd.DataFrame) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Perform production DBSCAN clustering with optimal parameters
    
    Returns:
        Tuple of (cluster_labels, clustering_metrics)
    """
    print("\n🎯 PERFORMING PRODUCTION CLUSTERING")
    print("="*50)
    print(f"   → Using optimal parameters: eps={JobClusteringProductionConfig.OPTIMAL_DBSCAN_PARAMS['eps']}, "
          f"min_samples={JobClusteringProductionConfig.OPTIMAL_DBSCAN_PARAMS['min_samples']}")
    
    # Convert similarity to distance matrix
    distance_matrix = 1 - similarity_df.values
    distance_matrix = np.maximum(distance_matrix, 0)
    
    # Perform DBSCAN clustering
    dbscan = DBSCAN(
        eps=JobClusteringProductionConfig.OPTIMAL_DBSCAN_PARAMS['eps'],
        min_samples=JobClusteringProductionConfig.OPTIMAL_DBSCAN_PARAMS['min_samples'],
        metric='precomputed'
    )
    
    cluster_labels = dbscan.fit_predict(distance_matrix)
    
    # Calculate clustering metrics
    n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
    noise_points = list(cluster_labels).count(-1)
    noise_ratio = noise_points / len(cluster_labels)
    
    # Calculate silhouette score for non-noise points
    silhouette = None
    if n_clusters > 1 and noise_points < len(cluster_labels):
        non_noise_mask = cluster_labels != -1
        if np.sum(non_noise_mask) > 1 and len(set(cluster_labels[non_noise_mask])) > 1:
            non_noise_distance = distance_matrix[non_noise_mask][:, non_noise_mask]
            non_noise_labels = cluster_labels[non_noise_mask]
            silhouette = silhouette_score(non_noise_distance, non_noise_labels, metric='precomputed')
    
    clustering_metrics = {
        'n_clusters': n_clusters,
        'noise_points': noise_points,
        'noise_ratio': noise_ratio,
        'silhouette_score': silhouette,
        'total_jobs': len(cluster_labels)
    }
    
    print(f"\n✅ CLUSTERING RESULTS:")
    print(f"   → Clusters found: {n_clusters}")
    print(f"   → Noise points: {noise_points} ({noise_ratio:.1%})")
    print(f"   → Silhouette score: {silhouette:.3f}" if silhouette else "   → Silhouette score: N/A")
    print(f"   → Expected clusters: {JobClusteringProductionConfig.EXPECTED_CLUSTERS}")
    print(f"   → Expected silhouette: {JobClusteringProductionConfig.EXPECTED_SILHOUETTE:.3f}")
    
    return cluster_labels, clustering_metrics

# =============================================================================
# ANALYSIS AND CHARACTERIZATION (Enhanced)
# =============================================================================

def analyze_job_clusters(
    cluster_labels: np.ndarray,
    job_metadata: pd.DataFrame,
    job_skills_df: pd.DataFrame,
    similarity_df: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Analyze and characterize job clusters with descriptive naming
    
    Returns:
        DataFrame with cluster analysis results including descriptive names
    """
    print("\n📊 ANALYZING JOB CLUSTERS WITH DESCRIPTIVE NAMING")
    print("="*60)
    
    # Create cluster assignments dataframe
    job_ids = similarity_df.index.tolist()
    cluster_df = pd.DataFrame({
        'JobProfileID': job_ids,
        'Cluster_ID': cluster_labels
    })
    
    # Merge with job metadata
    cluster_analysis = cluster_df.merge(job_metadata, on='JobProfileID', how='left')
    
    # Calculate cluster statistics with naming
    cluster_stats = []
    
    unique_clusters = sorted([c for c in set(cluster_labels) if c != -1])
    
    print(f"   → Generating descriptive names for {len(unique_clusters)} clusters...")
    
    for cluster_id in unique_clusters:
        cluster_jobs = cluster_analysis[cluster_analysis['Cluster_ID'] == cluster_id]
        cluster_size = len(cluster_jobs)
        
        # Generate descriptive name
        naming_result = generate_job_cluster_name(cluster_jobs, cluster_id)
        
        if cluster_size >= JobClusteringProductionConfig.MIN_CLUSTER_SIZE_ANALYSIS:
            # Get skills for jobs in this cluster
            cluster_job_ids = cluster_jobs['JobProfileID'].tolist()
            cluster_skills = job_skills_df[job_skills_df['JobProfileID'].isin(cluster_job_ids)]
            
            # Most common skills in cluster
            skill_counts = cluster_skills['Skill_Name'].value_counts()
            top_skills = skill_counts.head(JobClusteringProductionConfig.TOP_SKILLS_PER_CLUSTER).index.tolist()
            
            # Most common job functions
            function_counts = cluster_jobs['JobFunction'].value_counts()
            top_functions = function_counts.head(3).index.tolist()
            
            # Calculate intra-cluster similarity
            cluster_similarities = []
            for i in range(len(cluster_job_ids)):
                for j in range(i+1, len(cluster_job_ids)):
                    job_i, job_j = cluster_job_ids[i], cluster_job_ids[j]
                    if job_i in similarity_df.index and job_j in similarity_df.index:
                        sim = similarity_df.loc[job_i, job_j]
                        cluster_similarities.append(sim)
            
            avg_similarity = np.mean(cluster_similarities) if cluster_similarities else 0
            
            cluster_stats.append({
                'Cluster_ID': cluster_id,
                'Cluster_Name': naming_result['cluster_name'],
                'Cluster_Title': naming_result['cluster_title'],
                'Cluster_Description': naming_result['cluster_description'],
                'Naming_Confidence': naming_result['confidence'],
                'Naming_Rationale': naming_result['naming_rationale'],
                'Cluster_Size': cluster_size,
                'Avg_Intra_Similarity': avg_similarity,
                'Top_Functions': '; '.join(top_functions),
                'Top_Skills': '; '.join(top_skills[:5]),  # Top 5 for readability
                'Job_Examples': '; '.join(cluster_jobs['JobProfile'].head(3).tolist())
            })
        else:
            # Small cluster - still name it but mark as low confidence
            cluster_stats.append({
                'Cluster_ID': cluster_id,
                'Cluster_Name': naming_result['cluster_name'],
                'Cluster_Title': naming_result['cluster_title'],
                'Cluster_Description': naming_result['cluster_description'],
                'Naming_Confidence': 'Low',
                'Naming_Rationale': f"Small cluster ({cluster_size} jobs); {naming_result['naming_rationale']}",
                'Cluster_Size': cluster_size,
                'Avg_Intra_Similarity': 0,
                'Top_Functions': '; '.join(cluster_jobs['JobFunction'].value_counts().head(2).index.tolist()),
                'Top_Skills': 'Limited data',
                'Job_Examples': '; '.join(cluster_jobs['JobProfile'].head(3).tolist())
            })
    
    cluster_stats_df = pd.DataFrame(cluster_stats)
    
    # Add descriptive names back to main cluster analysis
    name_mapping = cluster_stats_df.set_index('Cluster_ID')['Cluster_Name'].to_dict()
    cluster_analysis['Cluster_Name'] = cluster_analysis['Cluster_ID'].map(name_mapping)
    cluster_analysis['Cluster_Name'] = cluster_analysis['Cluster_Name'].fillna('Noise/Unassigned')
    
    print(f"   → Generated descriptive names for all clusters")
    print(f"   → High confidence names: {len(cluster_stats_df[cluster_stats_df['Naming_Confidence'] == 'High'])}")
    print(f"   → Medium confidence names: {len(cluster_stats_df[cluster_stats_df['Naming_Confidence'] == 'Medium'])}")
    print(f"   → Low confidence names: {len(cluster_stats_df[cluster_stats_df['Naming_Confidence'] == 'Low'])}")
    
    return cluster_analysis, cluster_stats_df

# =============================================================================
# OUTPUT GENERATION (Enhanced)
# =============================================================================

def save_cluster_outputs(
    cluster_analysis: pd.DataFrame,
    cluster_stats: pd.DataFrame,
    clustering_metrics: Dict[str, Any],
    job_skills_df: pd.DataFrame
):
    """Save all clustering outputs to files with descriptive naming"""
    print("\n💾 SAVING CLUSTERING OUTPUTS WITH DESCRIPTIVE NAMES")
    print("="*55)
    
    timestamp = create_timestamp()
    
    # 1. Primary cluster assignments CSV (enhanced with structured names)
    output_df = cluster_analysis[['JobProfileID', 'JobProfile', 'JobFunction', 
                                 'JobSubFunction', 'JobCategory', 'ManagementLevel',
                                 'Cluster_ID', 'Cluster_Name']].copy()
    
    # Add structured naming fields
    title_mapping = cluster_stats.set_index('Cluster_ID')['Cluster_Title'].to_dict()
    description_mapping = cluster_stats.set_index('Cluster_ID')['Cluster_Description'].to_dict()
    
    output_df['Cluster_Title'] = output_df['Cluster_ID'].map(title_mapping)
    output_df['Cluster_Description'] = output_df['Cluster_ID'].map(description_mapping)
    output_df['Cluster_Title'] = output_df['Cluster_Title'].fillna('Unassigned')
    output_df['Cluster_Description'] = output_df['Cluster_Description'].fillna('No cluster assignment')
    
    # Add cluster size and quality metrics
    cluster_sizes = cluster_analysis['Cluster_ID'].value_counts().to_dict()
    output_df['Cluster_Size'] = output_df['Cluster_ID'].map(cluster_sizes)
    
    # Add naming confidence from cluster_stats
    name_confidence = cluster_stats.set_index('Cluster_ID')['Naming_Confidence'].to_dict()
    output_df['Naming_Confidence'] = output_df['Cluster_ID'].map(name_confidence)
    output_df['Naming_Confidence'] = output_df['Naming_Confidence'].fillna('N/A')
    
    output_df['Cluster_Quality'] = 'High' if clustering_metrics['silhouette_score'] > 0.8 else 'Good'
    
    primary_output_file = f"job_clusters_production_{timestamp}.csv"
    output_df.to_csv(primary_output_file, index=False)
    print(f"   → Primary output: {primary_output_file}")
    
    # 2. Enhanced cluster analysis report
    analysis_file = f"job_cluster_analysis_{timestamp}.txt"
    with open(analysis_file, 'w') as f:
        f.write("JOB PROFILE CLUSTERING - PRODUCTION ANALYSIS REPORT\n")
        f.write("="*60 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("CLUSTERING SUMMARY:\n")
        f.write(f"  Total Job Profiles: {clustering_metrics['total_jobs']}\n")
        f.write(f"  Clusters Found: {clustering_metrics['n_clusters']}\n")
        f.write(f"  Noise Points: {clustering_metrics['noise_points']} ({clustering_metrics['noise_ratio']:.1%})\n")
        f.write(f"  Silhouette Score: {clustering_metrics['silhouette_score']:.3f}\n")
        f.write(f"  Average Jobs per Cluster: {(clustering_metrics['total_jobs'] - clustering_metrics['noise_points']) / clustering_metrics['n_clusters']:.1f}\n\n")
        
        f.write("NAMING QUALITY SUMMARY:\n")
        naming_summary = cluster_stats['Naming_Confidence'].value_counts()
        for confidence, count in naming_summary.items():
            f.write(f"  {confidence} Confidence Names: {count} clusters\n")
        f.write("\n")
        
        f.write("PARAMETER VALIDATION:\n")
        f.write(f"  Expected Clusters: {JobClusteringProductionConfig.EXPECTED_CLUSTERS}\n")
        f.write(f"  Expected Silhouette: {JobClusteringProductionConfig.EXPECTED_SILHOUETTE:.3f}\n")
        f.write(f"  Expected Noise Ratio: {JobClusteringProductionConfig.EXPECTED_NOISE_RATIO:.1%}\n\n")
        
        f.write("TOP 20 CLUSTERS - STRUCTURED OVERVIEW:\n")
        for _, cluster in cluster_stats.head(20).iterrows():
            f.write(f"\nCluster {cluster['Cluster_ID']}: {cluster['Cluster_Title']}\n")
            f.write(f"  Description: {cluster['Cluster_Description']}\n")
            f.write(f"  Size: {cluster['Cluster_Size']} professionals\n")
            f.write(f"  Confidence: {cluster['Naming_Confidence']}\n")
            f.write("-" * 60 + "\n")
        
        f.write("\n\nEXECUTIVE SUMMARY - HIGH CONFIDENCE CLUSTERS:\n")
        high_conf_clusters = cluster_stats[cluster_stats['Naming_Confidence'] == 'High'].head(15)
        f.write(f"Found {len(high_conf_clusters)} high-confidence job cluster patterns:\n\n")
        
        for _, cluster in high_conf_clusters.iterrows():
            f.write(f"• {cluster['Cluster_Title']} ({cluster['Cluster_Size']} professionals)\n")
            f.write(f"  {cluster['Cluster_Description']}\n")
            f.write(f"  Representative roles: {cluster['Job_Examples']}\n\n")
        
        f.write("\n\nSTRATEGIC INSIGHTS:\n")
        f.write("  - Cluster names reflect natural job families based on organizational taxonomy\n")
        f.write("  - Use descriptive names for stakeholder communication and strategic planning\n")
        f.write("  - High confidence names indicate strong organizational patterns\n")
        f.write("  - Consider cluster names for career pathway design and workforce planning\n")
    
    print(f"   → Enhanced analysis report: {analysis_file}")
    
    # 3. Enhanced cluster characteristics CSV
    cluster_details_file = f"job_cluster_characteristics_{timestamp}.csv"
    cluster_stats.to_csv(cluster_details_file, index=False)
    print(f"   → Cluster details: {cluster_details_file}")
    
    # 4. Strategic cluster naming report
    naming_file = f"job_cluster_naming_report_{timestamp}.txt"
    with open(naming_file, 'w') as f:
        f.write("JOB CLUSTER NAMING ANALYSIS\n")
        f.write("="*35 + "\n\n")
        
        f.write("DESCRIPTIVE NAMING METHODOLOGY:\n")
        f.write("- Primary: JobFunction dominance (60% threshold)\n")
        f.write("- Secondary: JobSubFunction specialization\n")
        f.write("- Context: ManagementLevel patterns (Leadership/Specialists/Associate)\n")
        f.write("- Confidence: Based on cluster size and functional coherence\n\n")
        
        f.write("NAMING CONFIDENCE DISTRIBUTION:\n")
        for confidence in ['High', 'Medium', 'Low']:
            conf_clusters = cluster_stats[cluster_stats['Naming_Confidence'] == confidence]
            f.write(f"\n{confidence} Confidence ({len(conf_clusters)} clusters):\n")
            for _, cluster in conf_clusters.head(10).iterrows():
                f.write(f"  {cluster['Cluster_ID']}: {cluster['Cluster_Name']}\n")
        
        f.write("\n\nFUNCTIONAL DIVERSITY ANALYSIS:\n")
        # Analyze which JobFunctions appear in multiple clusters
        function_clusters = {}
        for _, cluster in cluster_stats.iterrows():
            top_functions = cluster['Top_Functions'].split('; ')
            for func in top_functions:
                if func not in function_clusters:
                    function_clusters[func] = []
                function_clusters[func].append(cluster['Cluster_ID'])
        
        f.write("JobFunctions appearing in multiple clusters:\n")
        for func, cluster_ids in function_clusters.items():
            if len(cluster_ids) > 1:
                f.write(f"  {func}: Clusters {cluster_ids}\n")
    
    print(f"   → Naming analysis: {naming_file}")
    
    print(f"\n✅ All outputs saved with descriptive naming and timestamp: {timestamp}")

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main execution function for production job profile clustering"""
    print("🚀 JOB PROFILE CLUSTERING - PRODUCTION")
    print("="*60)
    print(f"Target: {JobClusteringProductionConfig.EXPECTED_CLUSTERS} clusters with "
          f"{JobClusteringProductionConfig.EXPECTED_SILHOUETTE:.3f} silhouette score")
    print("="*60)
    
    try:
        # 1. Connect to database and load data
        conn = connect_database()
        job_skills_df, job_metadata_df = load_job_skill_data(conn)
        conn.close()
        
        # 2. Calculate defining skills
        job_defining_skills = calculate_defining_skills(job_skills_df)
        
        # 3. Create enhanced similarity matrix
        similarity_df, job_metadata = create_enhanced_similarity_matrix(
            job_skills_df, job_defining_skills
        )
        
        # 4. Perform production clustering
        cluster_labels, clustering_metrics = perform_production_clustering(similarity_df)
        
        # 5. Analyze clusters
        cluster_analysis, cluster_stats = analyze_job_clusters(
            cluster_labels, job_metadata, job_skills_df, similarity_df
        )
        
        # 6. Create visualizations (functionality moved to output generation)
        
        # 7. Save outputs
        save_cluster_outputs(cluster_analysis, cluster_stats, clustering_metrics, job_skills_df)
        
        print("\n🎉 PRODUCTION CLUSTERING COMPLETED SUCCESSFULLY!")
        print(f"   → Generated {clustering_metrics['n_clusters']} job clusters")
        print(f"   → Achieved {clustering_metrics['silhouette_score']:.3f} silhouette score")
        print(f"   → Ready for strategic workforce planning and pathway enhancement")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    main() 