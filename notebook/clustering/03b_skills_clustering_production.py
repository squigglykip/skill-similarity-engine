#!/usr/bin/env python3
"""
SKILLS CLUSTERING - PRODUCTION
==============================

Production-ready skills clustering using optimal parameters discovered through
comprehensive parameter optimization. Generates 193 skill bundles with 0.824 
silhouette score using cosine similarity and handles 38.1% specialized skills.

Purpose:
- Generate production skills clusters for L&D pathway design
- Implement optimal DBSCAN parameters (cosine similarity, eps=0.1, min_samples=3)
- Create skills bundle characterization and taxonomy analysis
- Handle specialized/emerging skills (noise) as separate category
- Output skills bundle assignments and learning pathway recommendations

Philosophy: Production clustering for evidence-based L&D design

Usage:
    python 03b_skills_clustering_production.py
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
from sklearn.metrics.pairwise import cosine_similarity
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

class SkillsClusteringProductionConfig:
    """Configuration for production skills clustering"""
    
    DATABASE_PATH = DATABASE_FILE
    
    # Optimal parameters from parameter optimization (hardcoded)
    OPTIMAL_DBSCAN_PARAMS = {
        'similarity_method': 'cosine',
        'eps': 0.1,
        'min_samples': 3
    }
    
    # Filtering thresholds
    MIN_JOBS_PER_SKILL = 3        # Skills must appear in at least 3 jobs
    MIN_COOCCURRENCE = 2          # Skill pairs must co-occur at least 2 times
    MAX_PREVALENCE = 80.0         # Exclude skills in >80% of jobs (too universal)
    
    # Expected results (from optimization)
    EXPECTED_CLUSTERS = 193
    EXPECTED_SILHOUETTE = 0.824
    EXPECTED_NOISE_RATIO = 0.381
    EXPECTED_TAXONOMY_ALIGNMENT = 0.563
    
    # Output settings
    SAVE_PLOTS = True
    PLOT_DPI = 300
    FIGURE_SIZE = (14, 10)
    
    # Analysis settings
    TOP_JOBS_PER_BUNDLE = 8       # Top job functions to show per skill bundle
    MIN_BUNDLE_SIZE_ANALYSIS = 5  # Minimum bundle size for detailed analysis
    MAX_BUNDLES_DETAILED = 20     # Maximum bundles for detailed analysis

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def connect_database():
    """Connect to the workforce intelligence database"""
    try:
        conn = sqlite3.connect(SkillsClusteringProductionConfig.DATABASE_PATH)
        print(f"✅ Connected to database: {SkillsClusteringProductionConfig.DATABASE_PATH}")
        return conn
    except sqlite3.OperationalError as e:
        raise FileNotFoundError(f"Could not connect to database: {e}")

def save_plot(fig, filename: str, title: Optional[str] = None):
    """Save plot with timestamp and title"""
    if title:
        fig.suptitle(title, fontsize=16, fontweight='bold')
    
    if SkillsClusteringProductionConfig.SAVE_PLOTS:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        full_filename = f"skills_clusters_production_{filename}_{timestamp}.png"
        fig.savefig(full_filename, dpi=SkillsClusteringProductionConfig.PLOT_DPI, bbox_inches='tight')
        print(f"   📊 Plot saved: {full_filename}")

def create_timestamp():
    """Create timestamp for output files"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

# =============================================================================
# DATA LOADING AND PROCESSING
# =============================================================================

def load_skills_data(conn) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load and filter skills data for clustering
    
    Returns:
        Tuple of (filtered_job_skills, skill_stats, cooccurrence_matrix)
    """
    print("📚 Loading and filtering skills data...")
    
    # Load job-skill relationships
    query = """
    SELECT 
        js.JobProfileID,
        js.Skill_ID,
        s.Skill_Name,
        s.Category,
        s.Subcategory,
        s.SkillType,
        j.JobFunction,
        j.JobSubFunction
    FROM job_skills js
    JOIN skills s ON js.Skill_ID = s.Skill_ID
    JOIN jobs j ON js.JobProfileID = j.JobProfileID
    WHERE js.JobProfileID IS NOT NULL 
      AND s.Skill_Name IS NOT NULL
    ORDER BY s.Skill_Name, js.JobProfileID
    """
    
    job_skills_df = pd.read_sql_query(query, conn)
    
    print(f"   → Loaded columns: {list(job_skills_df.columns)}")
    print(f"   → Raw job-skill relationships: {len(job_skills_df):,}")
    print(f"   → Raw unique skills: {job_skills_df['Skill_Name'].nunique():,}")
    
    # Calculate skill statistics - handle missing Subcategory gracefully
    agg_dict = {
        'JobProfileID': ['count', 'nunique'],
        'Category': 'first',
        'SkillType': 'first'
    }
    
    if 'Subcategory' in job_skills_df.columns:
        agg_dict['Subcategory'] = 'first'
        skill_stats = job_skills_df.groupby('Skill_Name').agg(agg_dict).round(3)
        skill_stats.columns = ['Total_Occurrences', 'Jobs_Count', 'Category', 'Subcategory', 'SkillType']
    else:
        print("   → Warning: Subcategory column not available, proceeding without it")
        skill_stats = job_skills_df.groupby('Skill_Name').agg(agg_dict).round(3)
        skill_stats.columns = ['Total_Occurrences', 'Jobs_Count', 'Category', 'SkillType']
    skill_stats = skill_stats.reset_index()
    
    total_jobs = job_skills_df['JobProfileID'].nunique()
    skill_stats['Prevalence_Percent'] = (skill_stats['Jobs_Count'] / total_jobs * 100)
    
    # Apply filtering criteria
    filtered_skills = skill_stats[
        (skill_stats['Jobs_Count'] >= SkillsClusteringProductionConfig.MIN_JOBS_PER_SKILL) &
        (skill_stats['Prevalence_Percent'] <= SkillsClusteringProductionConfig.MAX_PREVALENCE)
    ]['Skill_Name'].tolist()
    
    filtered_job_skills = job_skills_df[job_skills_df['Skill_Name'].isin(filtered_skills)]
    
    print(f"   → After filtering:")
    print(f"     • Skills remaining: {len(filtered_skills):,}")
    print(f"     • Job-skill relationships: {len(filtered_job_skills):,}")
    print(f"     • Jobs covered: {filtered_job_skills['JobProfileID'].nunique():,}")
    
    # Create co-occurrence matrix
    print("   → Building skill co-occurrence matrix...")
    
    # Create job-skill pivot
    job_skill_matrix = filtered_job_skills.pivot_table(
        index='JobProfileID', 
        columns='Skill_Name', 
        values='Skill_ID',
        fill_value=0,
        aggfunc='count'
    )
    
    # Convert to binary (skill present/absent)
    job_skill_binary = (job_skill_matrix > 0).astype(int)
    
    # Calculate co-occurrence matrix (skills x jobs)
    cooccurrence_matrix = job_skill_binary.T.values  # Transpose to get skills x jobs
    skill_names = job_skill_binary.columns.tolist()
    
    cooccurrence_df = pd.DataFrame(
        cooccurrence_matrix,
        index=skill_names,
        columns=job_skill_binary.index
    )
    
    # Update skill metadata to match filtered skills
    skill_metadata = skill_stats[skill_stats['Skill_Name'].isin(filtered_skills)].copy()
    skill_metadata = skill_metadata.set_index('Skill_Name')
    
    print(f"   → Co-occurrence matrix shape: {cooccurrence_df.shape}")
    
    return filtered_job_skills, skill_metadata, cooccurrence_df

def create_cosine_similarity_matrix(cooccurrence_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create cosine similarity matrix for skills
    
    Returns:
        Cosine similarity matrix DataFrame
    """
    print("🔗 Creating cosine similarity matrix...")
    
    skills_matrix = cooccurrence_df.values
    
    # Calculate cosine similarity
    cosine_matrix = cosine_similarity(skills_matrix)
    
    # Create DataFrame
    similarity_df = pd.DataFrame(
        cosine_matrix, 
        index=cooccurrence_df.index, 
        columns=cooccurrence_df.index
    )
    
    print(f"   → Cosine similarity matrix created: {similarity_df.shape}")
    print(f"   → Mean similarity: {np.mean(cosine_matrix[np.triu_indices_from(cosine_matrix, k=1)]):.3f}")
    
    return similarity_df

# =============================================================================
# CLUSTERING FUNCTIONS
# =============================================================================

def perform_production_clustering(similarity_df: pd.DataFrame) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Perform production DBSCAN clustering with optimal parameters
    
    Returns:
        Tuple of (cluster_labels, clustering_metrics)
    """
    print("\n🎯 PERFORMING PRODUCTION SKILLS CLUSTERING")
    print("="*50)
    print(f"   → Using optimal parameters: {SkillsClusteringProductionConfig.OPTIMAL_DBSCAN_PARAMS['similarity_method']} similarity, "
          f"eps={SkillsClusteringProductionConfig.OPTIMAL_DBSCAN_PARAMS['eps']}, "
          f"min_samples={SkillsClusteringProductionConfig.OPTIMAL_DBSCAN_PARAMS['min_samples']}")
    
    # Convert similarity to distance matrix
    distance_matrix = 1 - similarity_df.values
    distance_matrix = np.maximum(distance_matrix, 0)
    
    # Perform DBSCAN clustering
    dbscan = DBSCAN(
        eps=SkillsClusteringProductionConfig.OPTIMAL_DBSCAN_PARAMS['eps'],
        min_samples=SkillsClusteringProductionConfig.OPTIMAL_DBSCAN_PARAMS['min_samples'],
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
        'total_skills': len(cluster_labels)
    }
    
    print(f"\n✅ CLUSTERING RESULTS:")
    print(f"   → Skill bundles found: {n_clusters}")
    print(f"   → Specialized skills (noise): {noise_points} ({noise_ratio:.1%})")
    print(f"   → Silhouette score: {silhouette:.3f}" if silhouette else "   → Silhouette score: N/A")
    print(f"   → Expected bundles: {SkillsClusteringProductionConfig.EXPECTED_CLUSTERS}")
    print(f"   → Expected silhouette: {SkillsClusteringProductionConfig.EXPECTED_SILHOUETTE:.3f}")
    print(f"   → Expected noise ratio: {SkillsClusteringProductionConfig.EXPECTED_NOISE_RATIO:.1%}")
    
    return cluster_labels, clustering_metrics

# =============================================================================
# CLUSTER NAMING FUNCTIONS
# =============================================================================

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
    return float((cluster_data[column] == target_value).sum() / len(cluster_data))

def analyze_skill_type_pattern(cluster_skills: pd.DataFrame) -> str:
    """Analyze skill type patterns in cluster"""
    if len(cluster_skills) == 0:
        return "Mixed"
    
    skill_type_counts = cluster_skills['SkillType'].value_counts(normalize=True)
    
    if 'Specialized Skill' in skill_type_counts and skill_type_counts['Specialized Skill'] > 0.7:
        return "Advanced Skills"
    elif 'Certification' in skill_type_counts and skill_type_counts['Certification'] > 0.5:
        return "Certifications"
    elif 'Common Skill' in skill_type_counts and skill_type_counts['Common Skill'] > 0.4:
        return "Foundation Skills"
    else:
        return "Mixed Skills"

def get_top_subcategories(cluster_skills: pd.DataFrame, top_n: int = 2) -> List[str]:
    """Get top subcategories in cluster"""
    if len(cluster_skills) == 0:
        return []
    
    # Check if Subcategory column exists
    if 'Subcategory' not in cluster_skills.columns:
        print(f"   Warning: 'Subcategory' column not found. Available columns: {list(cluster_skills.columns)}")
        return []
    
    subcategory_counts = cluster_skills['Subcategory'].value_counts()
    return subcategory_counts.head(top_n).index.tolist()

def similar_themes(subcategories: List[str]) -> bool:
    """Check if subcategories have similar themes"""
    if len(subcategories) < 2:
        return True
    
    # Simple heuristic - check for common words
    words1 = set(subcategories[0].lower().split())
    words2 = set(subcategories[1].lower().split())
    common_words = words1.intersection(words2)
    
    return len(common_words) > 0

def combine_subcategories(subcategories: List[str]) -> str:
    """Combine similar subcategories into a coherent name"""
    if len(subcategories) == 0:
        return "General"
    elif len(subcategories) == 1:
        return subcategories[0]
    else:
        # Find common themes or use the more general one
        if similar_themes(subcategories):
            # Extract common words
            words1 = subcategories[0].lower().split()
            words2 = subcategories[1].lower().split()
            common_words = [w for w in words1 if w in words2]
            if common_words:
                return ' '.join(common_words).title()
        
        # Default to first subcategory if no clear combination
        return subcategories[0]

def analyze_skills_composition(cluster_skills: pd.DataFrame) -> Dict[str, Any]:
    """Analyze skills composition in human-readable terms"""
    if len(cluster_skills) == 0:
        return {'focus': 'undefined', 'breadth': 'none', 'primary_category': None}
    
    category_counts = cluster_skills['Category'].value_counts()
    total_skills = len(cluster_skills)
    
    # Determine focus level in professional terms
    if len(category_counts) == 1:
        focus = 'exclusively focused'
        breadth = 'specialized'
    elif category_counts.iloc[0] / total_skills >= 0.8:
        focus = 'predominantly centered'
        breadth = 'concentrated'
    elif category_counts.iloc[0] / total_skills >= 0.6:
        focus = 'primarily concentrated'
        breadth = 'focused'
    elif category_counts.iloc[0] / total_skills >= 0.4:
        focus = 'largely represented'
        breadth = 'diversified'
    else:
        focus = 'broadly encompassing'
        breadth = 'comprehensive'
    
    primary_category = category_counts.index[0] if len(category_counts) > 0 else None
    
    return {
        'focus': focus,
        'breadth': breadth,
        'primary_category': primary_category,
        'category_count': len(category_counts)
    }

def analyze_skills_application_level(cluster_skills: pd.DataFrame) -> str:
    """Determine the professional application level of skills"""
    if len(cluster_skills) == 0:
        return 'undefined'
    
    skill_type_counts = cluster_skills['SkillType'].value_counts(normalize=True)
    
    if 'Specialized Skill' in skill_type_counts and skill_type_counts['Specialized Skill'] >= 0.7:
        return 'advanced practice'
    elif 'Certification' in skill_type_counts and skill_type_counts['Certification'] >= 0.5:
        return 'professional certification'
    elif 'Common Skill' in skill_type_counts and skill_type_counts['Common Skill'] >= 0.4:
        return 'foundational competency'
    else:
        return 'mixed proficiency'

def create_skills_description(composition: Dict, application_level: str, specialization_area: str, bundle_size: int) -> str:
    """Create professional description for skills bundle"""
    
    # Start with the composition
    if composition['primary_category']:
        if composition['focus'] == 'exclusively focused':
            base_desc = f"comprehensive {composition['primary_category'].lower()} capabilities"
        elif composition['focus'] == 'predominantly centered':
            base_desc = f"core {composition['primary_category'].lower()} competencies with supporting skills"
        elif composition['focus'] == 'primarily concentrated':
            base_desc = f"essential {composition['primary_category'].lower()} skills complemented by related capabilities"
        elif composition['focus'] == 'largely represented':
            base_desc = f"diverse skill set emphasizing {composition['primary_category'].lower()} expertise"
        else:
            base_desc = f"multidisciplinary capabilities including strong {composition['primary_category'].lower()} foundation"
    else:
        base_desc = "cross-functional skill set spanning multiple domains"
    
    # Add specialization context
    if specialization_area and specialization_area != composition['primary_category']:
        area_short = specialization_area[:35] + "..." if len(specialization_area) > 35 else specialization_area
        base_desc += f", with particular strength in {area_short.lower()}"
    
    # Add application level
    if application_level == 'advanced practice':
        base_desc += ", requiring specialized expertise and deep technical knowledge"
    elif application_level == 'professional certification':
        base_desc += ", emphasizing credentialed competencies and industry standards"
    elif application_level == 'foundational competency':
        base_desc += ", representing essential workplace capabilities"
    elif application_level == 'mixed proficiency':
        base_desc += ", spanning various levels of technical depth and specialization"
    
    return base_desc

def generate_skills_bundle_name(cluster_skills: pd.DataFrame, cluster_id: int) -> Dict[str, str]:
    """
    Generate pragmatic, UK English naming for skills bundles
    
    Returns:
        Dict with 'name', 'description', 'rationale', and 'sample_skills'
    """
    if len(cluster_skills) == 0:
        return {
            'name': f"Empty Bundle {cluster_id}",
            'description': "No skills assigned to this bundle",
            'rationale': 'No skills in bundle',
            'sample_skills': ''
        }
    
    # Calculate bundle composition
    category_counts = cluster_skills['Category'].value_counts()
    total_skills = len(cluster_skills)
    dominant_category = category_counts.index[0] if not category_counts.empty else "Mixed"
    category_purity = category_counts.iloc[0] / total_skills if not category_counts.empty else 0
    
    # Determine confidence level and language
    if total_skills < 3:
        confidence_key = 'emerging'
        prefix = 'Emerging'
        suffix = 'Skills'
        description_starter = 'representing niche'
        qualifier = 'potentially'
    elif category_purity >= 0.8:
        confidence_key = 'high'
        prefix = ''
        suffix = 'Skills Bundle'
        description_starter = 'primarily focused on'
        qualifier = 'consistently'
    elif category_purity >= 0.6:
        confidence_key = 'medium'
        prefix = 'Mixed'
        suffix = 'Skills'
        description_starter = 'spanning across'
        qualifier = 'predominantly'
    else:
        confidence_key = 'low'
        prefix = 'Diverse'
        suffix = 'Skills Bundle'
        description_starter = 'covering various'
        qualifier = 'generally'
    
    # Create name
    if confidence_key == 'high':
        name = f"{dominant_category} {suffix}"
    else:
        name = f"{prefix} {dominant_category} {suffix}" if prefix else f"{dominant_category} {suffix}"
    
    # Format name in proper title case
    name = _format_title_case(name)
    
    # Create description
    description = f"Skills bundle {description_starter} {dominant_category.lower()}"
    
    # Create rationale
    rationale = f"{qualifier.capitalize()} {dominant_category.lower()} ({category_counts.iloc[0]}/{total_skills} skills, {category_purity:.1%} purity)"
    
    # Get sample skills
    sample_skills = '; '.join(cluster_skills['Skill_Name'].head(5).tolist() if 'Skill_Name' in cluster_skills.columns else [])
    
    return {
        'name': name,
        'description': description,
        'rationale': rationale,
        'sample_skills': sample_skills
    }

def _format_title_case(text: str) -> str:
    """Format text in proper title case for UK English"""
    if not text:
        return ""
    
    # Words that should remain lowercase in titles (UK style)
    lowercase_words = {'and', 'or', 'but', 'nor', 'for', 'yet', 'so', 'a', 'an', 'the', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
    
    words = text.split()
    formatted_words = []
    
    for i, word in enumerate(words):
        if i == 0 or word.lower() not in lowercase_words:
            # First word or content word - capitalise
            formatted_words.append(word.capitalize())
        else:
            # Articles, prepositions, conjunctions - keep lowercase
            formatted_words.append(word.lower())
    
    return ' '.join(formatted_words)

# =============================================================================
# ANALYSIS AND CHARACTERIZATION
# =============================================================================

def analyze_skill_bundles(
    cluster_labels: np.ndarray,
    skill_metadata: pd.DataFrame,
    job_skills_df: pd.DataFrame,
    similarity_df: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Analyze and characterize skill bundles with descriptive naming
    
    Returns:
        Tuple of (cluster_analysis, bundle_stats, specialized_skills)
    """
    print("\n📊 ANALYZING SKILL BUNDLES WITH PRAGMATIC NAMING")
    print("="*60)
    
    # Create cluster assignments dataframe
    skill_names = similarity_df.index.tolist()
    cluster_df = pd.DataFrame({
        'Skill_Name': skill_names,
        'Cluster_ID': cluster_labels
    })
    
    # Merge with skill metadata
    cluster_analysis = cluster_df.merge(
        skill_metadata.reset_index(), 
        on='Skill_Name', 
        how='left'
    )
    
    # Identify specialized/emerging skills (noise)
    specialized_skills = cluster_analysis[cluster_analysis['Cluster_ID'] == -1].copy()
    specialized_skills['Is_Specialized'] = True
    
    # Analyze skill bundles (non-noise clusters)
    bundle_stats = []
    unique_clusters = sorted([c for c in set(cluster_labels) if c != -1])
    
    print(f"   → Generating pragmatic names for {len(unique_clusters)} skill bundles...")
    
    for cluster_id in unique_clusters:
        cluster_skills = cluster_analysis[cluster_analysis['Cluster_ID'] == cluster_id]
        bundle_size = len(cluster_skills)
        
        # Generate pragmatic name
        naming_result = generate_skills_bundle_name(cluster_skills, cluster_id)
        
        # Get jobs that use skills in this bundle
        bundle_skill_names = cluster_skills['Skill_Name'].tolist() if 'Skill_Name' in cluster_skills.columns else []
        bundle_jobs = job_skills_df[job_skills_df['Skill_Name'].isin(bundle_skill_names)]
        
        # Most common job functions using these skills
        function_counts = bundle_jobs['JobFunction'].value_counts()
        top_functions = function_counts.head(3).index.tolist()
        sample_job_functions = '; '.join(top_functions)
        
        # Calculate intra-bundle similarity if bundle is large enough
        avg_similarity = 0
        if bundle_size >= SkillsClusteringProductionConfig.MIN_BUNDLE_SIZE_ANALYSIS:
            bundle_similarities = []
            for i in range(len(bundle_skill_names)):
                for j in range(i+1, len(bundle_skill_names)):
                    skill_i, skill_j = bundle_skill_names[i], bundle_skill_names[j]
                    if skill_i in similarity_df.index and skill_j in similarity_df.index:
                        sim = similarity_df.loc[skill_i, skill_j]
                        bundle_similarities.append(sim)
            avg_similarity = np.mean(bundle_similarities) if bundle_similarities else 0
        
        bundle_stats.append({
            'Cluster_ID': cluster_id,
            'Bundle_Name': naming_result['name'],
            'Bundle_Description': naming_result['description'],
            'Bundle_Rationale': naming_result['rationale'],
            'Sample_Skills': naming_result['sample_skills'],
            'Sample_Job_Functions': sample_job_functions if sample_job_functions else 'No job function data',
            'Bundle_Size': bundle_size,
            'Avg_Intra_Similarity': avg_similarity,
            'Jobs_Using_Bundle': bundle_jobs['JobProfileID'].nunique()
        })
    
    bundle_stats_df = pd.DataFrame(bundle_stats)
    
    print(f"   → Analyzed {len(unique_clusters)} skill bundles")
    print(f"   → Bundles with ≥{SkillsClusteringProductionConfig.MIN_BUNDLE_SIZE_ANALYSIS} skills: {len(bundle_stats_df)}")
    print(f"   → Specialized/emerging skills: {len(specialized_skills)}")
    
    return cluster_analysis, bundle_stats_df, specialized_skills

def calculate_taxonomy_alignment(
    cluster_analysis: pd.DataFrame,
    skill_metadata: pd.DataFrame
) -> float:
    """
    Calculate how well clusters align with existing skill taxonomy
    
    Returns:
        Taxonomy alignment score (0-1)
    """
    print("🎯 Calculating taxonomy alignment...")
    
    # Get non-noise clusters
    clustered_skills = cluster_analysis[cluster_analysis['Cluster_ID'] != -1]
    
    if len(clustered_skills) == 0:
        return 0.0
    
    # Calculate purity score for each cluster
    alignment_scores = []
    
    for cluster_id in clustered_skills['Cluster_ID'].unique():
        cluster_skills = clustered_skills[clustered_skills['Cluster_ID'] == cluster_id]
        
        if len(cluster_skills) > 1:
            # Most common category in cluster
            category_counts = cluster_skills['Category'].value_counts()
            most_common_category = category_counts.iloc[0]
            total_skills = len(cluster_skills)
            
            # Purity = fraction of skills in most common category
            purity = most_common_category / total_skills
            alignment_scores.append(purity)
    
    overall_alignment = np.mean(alignment_scores) if alignment_scores else 0.0
    
    print(f"   → Taxonomy alignment score: {overall_alignment:.3f}")
    print(f"   → Expected alignment: {SkillsClusteringProductionConfig.EXPECTED_TAXONOMY_ALIGNMENT:.3f}")
    
    return overall_alignment

def create_skills_visualizations(
    cluster_analysis: pd.DataFrame,
    bundle_stats: pd.DataFrame,
    specialized_skills: pd.DataFrame,
    clustering_metrics: Dict[str, Any],
    taxonomy_alignment: float
):
    """Create comprehensive skills clustering visualizations"""
    print("\n📈 Creating skills clustering visualizations...")
    
    # Figure 1: Overview and bundle characteristics
    fig1, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=SkillsClusteringProductionConfig.FIGURE_SIZE)
    
    # Bundle size distribution
    bundle_sizes = cluster_analysis[cluster_analysis['Cluster_ID'] != -1]['Cluster_ID'].value_counts()
    ax1.hist(bundle_sizes.values, bins=15, alpha=0.7, color='lightcoral', edgecolor='black')
    ax1.set_xlabel('Bundle Size (Number of Skills)')
    ax1.set_ylabel('Number of Bundles')
    ax1.set_title('Distribution of Skill Bundle Sizes')
    ax1.grid(True, alpha=0.3)
    
    # Category distribution in bundles vs specialized
    bundled_categories = cluster_analysis[cluster_analysis['Cluster_ID'] != -1]['Category'].value_counts().head(8)
    specialized_categories = specialized_skills['Category'].value_counts().head(8)
    
    x_pos = np.arange(len(bundled_categories))
    width = 0.35
    
    ax2.bar(x_pos - width/2, bundled_categories.values, width, label='In Bundles', alpha=0.7, color='skyblue')
    if len(specialized_categories) > 0:
        # Align specialized categories with bundled ones
        specialized_aligned = [specialized_categories.get(cat, 0) for cat in bundled_categories.index]
        ax2.bar(x_pos + width/2, specialized_aligned, width, label='Specialized', alpha=0.7, color='orange')
    
    ax2.set_xlabel('Skill Categories')
    ax2.set_ylabel('Number of Skills')
    ax2.set_title('Skills by Category: Bundled vs Specialized')
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(bundled_categories.index, rotation=45, ha='right', fontsize=8)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # Clustering quality metrics
    metrics_text = f"""Skills Clustering Quality:
    
Bundles Found: {clustering_metrics['n_clusters']}
Expected: {SkillsClusteringProductionConfig.EXPECTED_CLUSTERS}

Silhouette Score: {clustering_metrics['silhouette_score']:.3f}
Expected: {SkillsClusteringProductionConfig.EXPECTED_SILHOUETTE:.3f}

Specialized Skills: {clustering_metrics['noise_ratio']:.1%}
Expected: {SkillsClusteringProductionConfig.EXPECTED_NOISE_RATIO:.1%}

Taxonomy Alignment: {taxonomy_alignment:.3f}
Expected: {SkillsClusteringProductionConfig.EXPECTED_TAXONOMY_ALIGNMENT:.3f}

Total Skills: {clustering_metrics['total_skills']}
"""
    ax3.text(0.05, 0.95, metrics_text, transform=ax3.transAxes, fontsize=9,
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))
    ax3.set_xlim(0, 1)
    ax3.set_ylim(0, 1)
    ax3.axis('off')
    ax3.set_title('Clustering Performance')
    
    # Top bundles by job coverage
    if len(bundle_stats) > 0:
        top_bundles = bundle_stats.nlargest(10, 'Jobs_Using_Bundle')
        ax4.barh(range(len(top_bundles)), top_bundles['Jobs_Using_Bundle'].values, color='lightseagreen')
        ax4.set_yticks(range(len(top_bundles)))
        ax4.set_yticklabels([f"Bundle {bid}" for bid in top_bundles['Cluster_ID']], fontsize=8)
        ax4.set_xlabel('Number of Jobs Using Bundle')
        ax4.set_title('Top 10 Bundles by Job Coverage')
        ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    save_plot(fig1, 'overview', 'Skills Clustering - Production Results')
    
    # Figure 2: Bundle themes and characteristics
    if len(bundle_stats) >= 5:
        fig2, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # Bundle similarity vs size scatter plot
        ax1.scatter(bundle_stats['Bundle_Size'], bundle_stats['Avg_Intra_Similarity'], 
                   alpha=0.7, s=60, color='purple')
        ax1.set_xlabel('Bundle Size (Number of Skills)')
        ax1.set_ylabel('Average Intra-Bundle Similarity')
        ax1.set_title('Bundle Quality: Size vs Internal Similarity')
        ax1.grid(True, alpha=0.3)
        
        # Top bundles characteristics
        top_bundles_display = bundle_stats.nlargest(10, 'Bundle_Size')
        y_pos = np.arange(len(top_bundles_display))
        
        ax2.barh(y_pos, top_bundles_display['Bundle_Size'].values, color='coral', alpha=0.7)
        ax2.set_yticks(y_pos)
        bundle_labels = [f"{row['Bundle_Name'][:25]}..." if len(row['Bundle_Name']) > 25 
                        else row['Bundle_Name'] for _, row in top_bundles_display.iterrows()]
        ax2.set_yticklabels(bundle_labels, fontsize=9)
        ax2.set_xlabel('Bundle Size')
        ax2.set_title('Top 10 Largest Skill Bundles')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        save_plot(fig2, 'characteristics', 'Skill Bundle Characteristics Analysis')

# =============================================================================
# OUTPUT GENERATION
# =============================================================================

def save_skills_outputs(
    cluster_analysis: pd.DataFrame,
    bundle_stats: pd.DataFrame,
    specialized_skills: pd.DataFrame,
    clustering_metrics: Dict[str, Any],
    taxonomy_alignment: float,
    job_skills_df: pd.DataFrame
):
    """Save all skills clustering outputs to files"""
    print("\n💾 SAVING SKILLS CLUSTERING OUTPUTS WITH PRAGMATIC NAMING")
    print("="*55)
    
    timestamp = create_timestamp()
    
    # 1. Primary skills cluster assignments CSV with pragmatic naming
    output_df = cluster_analysis.copy()
    output_df['Is_Specialized'] = output_df['Cluster_ID'] == -1
    
    # Add bundle information from bundle_stats
    bundle_name_mapping = bundle_stats.set_index('Cluster_ID')['Bundle_Name'].to_dict()
    bundle_description_mapping = bundle_stats.set_index('Cluster_ID')['Bundle_Description'].to_dict()
    bundle_rationale_mapping = bundle_stats.set_index('Cluster_ID')['Bundle_Rationale'].to_dict()
    sample_skills_mapping = bundle_stats.set_index('Cluster_ID')['Sample_Skills'].to_dict()
    sample_functions_mapping = bundle_stats.set_index('Cluster_ID')['Sample_Job_Functions'].to_dict()
    bundle_size_mapping = bundle_stats.set_index('Cluster_ID')['Bundle_Size'].to_dict()
    
    # Apply mappings with defaults for specialized/small bundles
    output_df['Bundle_Name'] = output_df['Cluster_ID'].map(bundle_name_mapping)
    output_df['Bundle_Description'] = output_df['Cluster_ID'].map(bundle_description_mapping)
    output_df['Bundle_Rationale'] = output_df['Cluster_ID'].map(bundle_rationale_mapping)
    output_df['Sample_Skills'] = output_df['Cluster_ID'].map(sample_skills_mapping)
    output_df['Sample_Job_Functions'] = output_df['Cluster_ID'].map(sample_functions_mapping)
    output_df['Bundle_Size'] = output_df['Cluster_ID'].map(bundle_size_mapping)
    
    # Fill defaults for specialized and small bundles
    output_df['Bundle_Name'] = output_df['Bundle_Name'].fillna(output_df.apply(
        lambda row: 'Specialised/Emerging Skill' if row['Cluster_ID'] == -1 else f'Small Bundle {row["Cluster_ID"]}', axis=1
    ))
    output_df['Bundle_Description'] = output_df['Bundle_Description'].fillna(
        'Specialised or emerging skill not grouped into a bundle'
    )
    output_df['Bundle_Rationale'] = output_df['Bundle_Rationale'].fillna('Single skill or small cluster')
    output_df['Sample_Skills'] = output_df['Sample_Skills'].fillna('')
    output_df['Sample_Job_Functions'] = output_df['Sample_Job_Functions'].fillna('')
    output_df['Bundle_Size'] = output_df['Bundle_Size'].fillna(1)
    
    primary_output_file = f"skills_clusters_production_{timestamp}.csv"
    output_df.to_csv(primary_output_file, index=False)
    print(f"   → Primary output: {primary_output_file}")
    
    # 2. Skills bundle analysis report
    analysis_file = f"skills_bundles_analysis_{timestamp}.txt"
    with open(analysis_file, 'w') as f:
        f.write("SKILLS CLUSTERING - PRODUCTION ANALYSIS REPORT\n")
        f.write("="*60 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("CLUSTERING SUMMARY:\n")
        f.write(f"  Total Skills Analyzed: {clustering_metrics['total_skills']}\n")
        f.write(f"  Skill Bundles Found: {clustering_metrics['n_clusters']}\n")
        f.write(f"  Specialized/Emerging Skills: {clustering_metrics['noise_points']} ({clustering_metrics['noise_ratio']:.1%})\n")
        f.write(f"  Silhouette Score: {clustering_metrics['silhouette_score']:.3f}\n")
        f.write(f"  Taxonomy Alignment: {taxonomy_alignment:.3f}\n")
        f.write(f"  Average Skills per Bundle: {(clustering_metrics['total_skills'] - clustering_metrics['noise_points']) / clustering_metrics['n_clusters']:.1f}\n\n")
        
        f.write("PARAMETER VALIDATION:\n")
        f.write(f"  Expected Bundles: {SkillsClusteringProductionConfig.EXPECTED_CLUSTERS}\n")
        f.write(f"  Expected Silhouette: {SkillsClusteringProductionConfig.EXPECTED_SILHOUETTE:.3f}\n")
        f.write(f"  Expected Noise Ratio: {SkillsClusteringProductionConfig.EXPECTED_NOISE_RATIO:.1%}\n")
        f.write(f"  Expected Taxonomy Alignment: {SkillsClusteringProductionConfig.EXPECTED_TAXONOMY_ALIGNMENT:.3f}\n\n")
        
        f.write("TOP 15 SKILL BUNDLES:\n")
        display_bundles = bundle_stats.head(15) if len(bundle_stats) >= 15 else bundle_stats
        f.write(display_bundles[['Cluster_ID', 'Bundle_Size', 'Bundle_Name', 'Sample_Job_Functions', 'Jobs_Using_Bundle']].to_string(index=False))
        
        f.write("\n\nL&D PATHWAY RECOMMENDATIONS:\n")
        f.write("  - Use skill bundles to design comprehensive learning curricula\n")
        f.write("  - Focus on bundles with high job coverage for maximum impact\n")
        f.write("  - Consider specialized skills for advanced/niche training programs\n")
        f.write("  - Bundle themes suggest natural learning progression pathways\n")
    
    print(f"   → Analysis report: {analysis_file}")
    
    # 3. Specialized/emerging skills CSV
    specialized_output_file = f"specialized_emerging_skills_{timestamp}.csv"
    specialized_skills[['Skill_Name', 'Category', 'Jobs_Count', 'Prevalence_Percent']].to_csv(
        specialized_output_file, index=False
    )
    print(f"   → Specialized skills: {specialized_output_file}")
    
    # 4. Skill bundle characteristics CSV
    bundle_details_file = f"skill_bundles_characteristics_{timestamp}.csv"
    bundle_stats.to_csv(bundle_details_file, index=False)
    print(f"   → Bundle details: {bundle_details_file}")
    
    # 5. Learning pathway recommendations
    pathways_file = f"learning_pathway_recommendations_{timestamp}.txt"
    with open(pathways_file, 'w') as f:
        f.write("LEARNING PATHWAY RECOMMENDATIONS\n")
        f.write("="*40 + "\n\n")
        f.write("Based on skill bundle analysis, here are strategic L&D recommendations:\n\n")
        
        # Top bundles by job coverage for foundational skills
        if len(bundle_stats) > 0:
            foundational_bundles = bundle_stats.nlargest(5, 'Jobs_Using_Bundle')
            f.write("FOUNDATIONAL SKILLS PATHWAYS (High Job Coverage):\n")
            for _, bundle in foundational_bundles.iterrows():
                f.write(f"\n{bundle['Bundle_Name']} Bundle (ID: {bundle['Cluster_ID']}):\n")
                f.write(f"  - Bundle Size: {bundle['Bundle_Size']} skills\n")
                f.write(f"  - Job Coverage: {bundle['Jobs_Using_Bundle']} different job profiles\n")
                f.write(f"  - Primary Functions: {bundle['Sample_Job_Functions']}\n")
                f.write(f"  - Learning Priority: HIGH (widespread applicability)\n")
            
            # Specialized bundles for advanced pathways
            specialized_bundles = bundle_stats.nsmallest(5, 'Jobs_Using_Bundle')
            f.write(f"\n\nSPECIALISED SKILLS PATHWAYS (Targeted Coverage):\n")
            for _, bundle in specialized_bundles.iterrows():
                f.write(f"\n{bundle['Bundle_Name']} Bundle (ID: {bundle['Cluster_ID']}):\n")
                f.write(f"  - Bundle Size: {bundle['Bundle_Size']} skills\n")
                f.write(f"  - Job Coverage: {bundle['Jobs_Using_Bundle']} specific job profiles\n")
                f.write(f"  - Primary Functions: {bundle['Sample_Job_Functions']}\n")
                f.write(f"  - Learning Priority: TARGETED (specialised roles)\n")
        
        f.write(f"\n\nEMERGING/SPECIALIZED SKILLS ({len(specialized_skills)} skills):\n")
        f.write("  - Consider for innovation and future-skills programs\n")
        f.write("  - May represent cutting-edge capabilities or highly specialized roles\n")
        f.write("  - Evaluate for strategic importance and development investment\n")
    
    print(f"   → Learning pathways: {pathways_file}")
    
    print(f"\n✅ All skills clustering outputs saved with timestamp: {timestamp}")

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main execution function for production skills clustering"""
    print("🚀 SKILLS CLUSTERING - PRODUCTION")
    print("="*60)
    print(f"Target: {SkillsClusteringProductionConfig.EXPECTED_CLUSTERS} skill bundles with "
          f"{SkillsClusteringProductionConfig.EXPECTED_SILHOUETTE:.3f} silhouette score")
    print("="*60)
    
    try:
        # 1. Connect to database and load data
        conn = connect_database()
        job_skills_df, skill_metadata, cooccurrence_df = load_skills_data(conn)
        conn.close()
        
        # 2. Create cosine similarity matrix
        similarity_df = create_cosine_similarity_matrix(cooccurrence_df)
        
        # 3. Perform production clustering
        cluster_labels, clustering_metrics = perform_production_clustering(similarity_df)
        
        # 4. Analyze skill bundles
        cluster_analysis, bundle_stats, specialized_skills = analyze_skill_bundles(
            cluster_labels, skill_metadata, job_skills_df, similarity_df
        )
        
        # 5. Calculate taxonomy alignment
        taxonomy_alignment = calculate_taxonomy_alignment(cluster_analysis, skill_metadata)
        
        # 6. Create visualizations
        create_skills_visualizations(
            cluster_analysis, bundle_stats, specialized_skills, 
            clustering_metrics, taxonomy_alignment
        )
        
        # 7. Save outputs
        save_skills_outputs(
            cluster_analysis, bundle_stats, specialized_skills,
            clustering_metrics, taxonomy_alignment, job_skills_df
        )
        
        print("\n🎉 PRODUCTION SKILLS CLUSTERING COMPLETED SUCCESSFULLY!")
        print(f"   → Generated {clustering_metrics['n_clusters']} skill bundles")
        print(f"   → Achieved {clustering_metrics['silhouette_score']:.3f} silhouette score")
        print(f"   → Identified {clustering_metrics['noise_points']} specialized/emerging skills")
        print(f"   → Taxonomy alignment: {taxonomy_alignment:.3f}")
        print(f"   → Ready for L&D pathway design and skills taxonomy refinement")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    main() 