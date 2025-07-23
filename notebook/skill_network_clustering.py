#!/usr/bin/env python3
"""
SKILL NETWORK CLUSTERING - Supplemental Intelligence  
=====================================================

Network analysis of skill co-occurrence patterns to identify natural skill families,
bundles, and ecosystem connections across the organisation.

Philosophy: Descriptive ecosystem intelligence for architectural thinking.
Shows how skills naturally cluster, not which clusters are "best."

Usage:
    python skill_network_clustering.py
"""

import pandas as pd
import numpy as np
import sqlite3
import warnings
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Set, Any
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict

warnings.filterwarnings('ignore')

# =============================================================================
# CONFIGURATION  
# =============================================================================

DATABASE_FILE = "models/2025-Q3/workforce_intelligence.sqlite"

class NetworkClusteringConfig:
    """Configuration for Skill Network Clustering"""
    
    DATABASE_PATH = DATABASE_FILE
    
    # DBSCAN clustering parameters
    DBSCAN_PARAMS = {
        'eps': 0.3,           # Maximum distance for clustering
        'min_samples': 3,     # Minimum skills per cluster
        'metric': 'cosine'    # Distance metric
    }
    
    # Co-occurrence thresholds
    COOCCURRENCE_THRESHOLDS = {
        'min_job_profiles': 5,    # Minimum job profiles for meaningful co-occurrence
        'min_cooccurrence': 0.1   # Minimum co-occurrence rate (10%)
    }

# =============================================================================
# CORE FUNCTIONS
# =============================================================================

def connect_database():
    """Connect to the workforce intelligence database"""
    try:
        conn = sqlite3.connect(NetworkClusteringConfig.DATABASE_PATH)
        print(f"✅ Connected to database: {NetworkClusteringConfig.DATABASE_PATH}")
        return conn
    except sqlite3.OperationalError as e:
        raise FileNotFoundError(f"Could not connect to database: {e}")

def build_skill_cooccurrence_matrix(conn) -> Tuple[pd.DataFrame, List[str]]:
    """
    Build skill co-occurrence matrix from job-skill relationships
    
    Returns:
        Tuple of (cooccurrence_matrix, skill_names)
    """
    print("🔗 Building skill co-occurrence matrix...")
    
    # Load job-skill relationships
    job_skills_query = """
    SELECT 
        j.JobProfileID,
        s.Skill_Name
    FROM jobs j
    JOIN job_skills js ON j.JobProfileID = js.JobProfileID
    JOIN skills s ON js.Skill_ID = s.Skill_ID
    ORDER BY j.JobProfileID, s.Skill_Name
    """
    
    job_skills_df = pd.read_sql_query(job_skills_query, conn)
    
    # Create job-skill matrix (binary)
    job_skill_matrix = job_skills_df.groupby(['JobProfileID', 'Skill_Name']).size().unstack(fill_value=0)
    job_skill_matrix = (job_skill_matrix > 0).astype(int)  # Convert to binary
    
    # Calculate co-occurrence matrix (skill x skill)
    cooccurrence_matrix = np.dot(job_skill_matrix.T, job_skill_matrix)
    
    # Convert to DataFrame
    skill_names = job_skill_matrix.columns.tolist()
    cooccurrence_df = pd.DataFrame(
        cooccurrence_matrix, 
        index=skill_names, 
        columns=skill_names
    )
    
    print(f"   → Built matrix for {len(skill_names):,} skills")
    print(f"   → Analyzed {len(job_skill_matrix):,} job profiles")
    
    return cooccurrence_df, skill_names

def calculate_skill_similarity_matrix(cooccurrence_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate skill similarity matrix using cosine similarity
    
    Returns:
        Skill similarity matrix
    """
    print("📊 Calculating skill similarity matrix...")
    
    # Use cosine similarity on co-occurrence vectors
    similarity_matrix = cosine_similarity(cooccurrence_df.values)
    
    similarity_df = pd.DataFrame(
        similarity_matrix,
        index=cooccurrence_df.index,
        columns=cooccurrence_df.columns
    )
    
    print(f"   → Calculated similarity for {len(similarity_df):,} x {len(similarity_df):,} skill pairs")
    
    return similarity_df

def cluster_skills_dbscan(similarity_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Cluster skills using DBSCAN algorithm
    
    Returns:
        Dict with clustering results
    """
    print("🎯 Clustering skills using DBSCAN...")
    
    # Convert similarity to distance (1 - similarity) and ensure non-negative
    distance_matrix = 1 - similarity_df.values
    distance_matrix = np.clip(distance_matrix, 0, None)  # Ensure non-negative
    
    # Fill diagonal with zeros (distance from skill to itself)
    np.fill_diagonal(distance_matrix, 0)
    
    print(f"   → Distance matrix shape: {distance_matrix.shape}")
    print(f"   → Distance range: {distance_matrix.min():.3f} to {distance_matrix.max():.3f}")
    
    # Apply DBSCAN clustering
    dbscan = DBSCAN(
        eps=NetworkClusteringConfig.DBSCAN_PARAMS['eps'],
        min_samples=NetworkClusteringConfig.DBSCAN_PARAMS['min_samples'],
        metric='precomputed'
    )
    
    cluster_labels = dbscan.fit_predict(distance_matrix)
    
    # Create clustering results
    skill_names = similarity_df.index.tolist()
    clustering_results = pd.DataFrame({
        'Skill_Name': skill_names,
        'Cluster_ID': cluster_labels
    })
    
    # Analyze clusters
    n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
    n_noise = list(cluster_labels).count(-1)
    
    print(f"   → Identified {n_clusters:,} skill clusters")
    print(f"   → {n_noise:,} skills classified as noise/outliers")
    
    # Generate cluster characterization
    clusters = {}
    for cluster_id in set(cluster_labels):
        if cluster_id == -1:  # Skip noise
            continue
            
        cluster_skills = clustering_results[
            clustering_results['Cluster_ID'] == cluster_id
        ]['Skill_Name'].tolist()
        
        clusters[f"Cluster_{cluster_id}"] = {
            'cluster_id': cluster_id,
            'skills': cluster_skills,
            'size': len(cluster_skills)
        }
    
    return {
        'clustering_df': clustering_results,
        'clusters': clusters,
        'n_clusters': n_clusters,
        'n_noise': n_noise,
        'cluster_summary': {k: v['size'] for k, v in clusters.items()}
    }

def identify_bridge_skills(similarity_df: pd.DataFrame, clustering_results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Identify bridge skills that connect different clusters
    
    Returns:
        List of bridge skills with their connection metrics
    """
    print("🌉 Identifying bridge skills...")
    
    clustering_df = clustering_results['clustering_df']
    bridge_skills = []
    
    # For each skill, calculate its average similarity to other clusters
    for idx, row in clustering_df.iterrows():
        skill_name = row['Skill_Name']
        skill_cluster = row['Cluster_ID']
        
        if skill_cluster == -1:  # Skip noise skills
            continue
        
        # Calculate average similarity to skills in other clusters
        other_cluster_similarities = []
        
        for other_cluster_id in clustering_df['Cluster_ID'].unique():
            if other_cluster_id == skill_cluster or other_cluster_id == -1:
                continue
                
            other_cluster_skills = clustering_df[
                clustering_df['Cluster_ID'] == other_cluster_id
            ]['Skill_Name'].tolist()
            
            if other_cluster_skills:
                avg_similarity = similarity_df.loc[skill_name, other_cluster_skills].mean()
                other_cluster_similarities.append(avg_similarity)
        
        if other_cluster_similarities:
            avg_cross_cluster_similarity = np.mean(other_cluster_similarities)
            max_cross_cluster_similarity = np.max(other_cluster_similarities)
            
            bridge_skills.append({
                'skill_name': skill_name,
                'home_cluster': skill_cluster,
                'avg_cross_cluster_similarity': avg_cross_cluster_similarity,
                'max_cross_cluster_similarity': max_cross_cluster_similarity,
                'bridge_potential': avg_cross_cluster_similarity  # Could be weighted differently
            })
    
    # Sort by bridge potential
    bridge_skills.sort(key=lambda x: x['bridge_potential'], reverse=True)
    
    print(f"   → Analyzed {len(bridge_skills):,} potential bridge skills")
    
    return bridge_skills[:20]  # Return top 20 bridge skills

def generate_network_summary(
    cooccurrence_df: pd.DataFrame,
    clustering_results: Dict[str, Any],
    bridge_skills: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Generate network clustering summary
    
    Returns:
        Dict with network insights
    """
    print("📊 Generating network clustering summary...")
    
    clusters = clustering_results['clusters']
    
    # Characterize top clusters by size
    top_clusters = sorted(clusters.items(), key=lambda x: x[1]['size'], reverse=True)[:5]
    
    summary = {
        'total_skills_analyzed': len(cooccurrence_df),
        'total_clusters_identified': clustering_results['n_clusters'],
        'skills_in_clusters': sum(cluster['size'] for cluster in clusters.values()),
        'noise_skills': clustering_results['n_noise'],
        'clustering_efficiency': (sum(cluster['size'] for cluster in clusters.values()) / len(cooccurrence_df)) * 100,
        'top_clusters': {name: info['size'] for name, info in top_clusters},
        'top_bridge_skills': [skill['skill_name'] for skill in bridge_skills[:10]],
        'avg_cluster_size': np.mean([cluster['size'] for cluster in clusters.values()]) if clusters else 0
    }
    
    return summary

# =============================================================================
# MAIN ANALYSIS FUNCTION  
# =============================================================================

def run_network_clustering(output_prefix: str = "skill_network") -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Main network clustering analysis function
    
    Returns:
        Tuple of (clustering_results, summary)
    """
    print("🕸️  SKILL NETWORK CLUSTERING - ECOSYSTEM INTELLIGENCE")
    print("="*65)
    print("🎯 Purpose: Map natural skill families and ecosystems")
    print("🔍 Method: Co-occurrence analysis with DBSCAN clustering")
    
    conn = connect_database()
    
    try:
        # Build co-occurrence matrix
        cooccurrence_df, skill_names = build_skill_cooccurrence_matrix(conn)
        
        # Calculate similarity matrix
        similarity_df = calculate_skill_similarity_matrix(cooccurrence_df)
        
        # Cluster skills
        clustering_results = cluster_skills_dbscan(similarity_df)
        
        # Identify bridge skills
        bridge_skills = identify_bridge_skills(similarity_df, clustering_results)
        
        # Generate summary
        summary = generate_network_summary(cooccurrence_df, clustering_results, bridge_skills)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save clustering results
        clustering_output_path = f"{output_prefix}_clusters_{timestamp}.csv"
        clustering_results['clustering_df'].to_csv(clustering_output_path, index=False)
        print(f"💾 Clustering results saved: {clustering_output_path}")
        
        # Save bridge skills
        bridge_output_path = f"{output_prefix}_bridge_skills_{timestamp}.csv"
        pd.DataFrame(bridge_skills).to_csv(bridge_output_path, index=False)
        print(f"💾 Bridge skills saved: {bridge_output_path}")
        
        # Display insights
        print(f"\n📊 NETWORK CLUSTERING SUMMARY")
        print("-" * 45)
        print(f"🎯 Skills analyzed: {summary['total_skills_analyzed']:,}")
        print(f"🎪 Clusters identified: {summary['total_clusters_identified']:,}")
        print(f"📦 Skills in clusters: {summary['skills_in_clusters']:,}")
        print(f"🌀 Noise/outlier skills: {summary['noise_skills']:,}")
        print(f"⚡ Clustering efficiency: {summary['clustering_efficiency']:.1f}%")
        print(f"📏 Average cluster size: {summary['avg_cluster_size']:.1f} skills")
        
        print(f"\n🏆 Top 5 Skill Clusters by Size:")
        for cluster_name, size in list(summary['top_clusters'].items())[:5]:
            print(f"   • {cluster_name}: {size} skills")
        
        print(f"\n🌉 Top 5 Bridge Skills (Cross-Cluster Connectors):")
        for skill in summary['top_bridge_skills'][:5]:
            print(f"   • {skill}")
        
        # Show example clusters
        if clustering_results['clusters']:
            print(f"\n🎯 Example Skill Clusters:")
            for cluster_name, cluster_info in list(clustering_results['clusters'].items())[:3]:
                skills_preview = ', '.join(cluster_info['skills'][:5])
                if len(cluster_info['skills']) > 5:
                    skills_preview += f", ... (+{len(cluster_info['skills'])-5} more)"
                print(f"   • {cluster_name} ({cluster_info['size']} skills): {skills_preview}")
        
        return clustering_results, summary
        
    finally:
        conn.close()
        print(f"\n🔒 Database connection closed")

# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    print("🕸️  SKILL NETWORK CLUSTERING - SUPPLEMENTAL INTELLIGENCE")
    print("="*65)
    print("🎯 Ecosystem mapping for architectural thinking")
    print("🔍 Natural skill families and cross-domain connections")
    print()
    
    # Run network clustering analysis
    clustering_results, summary = run_network_clustering()
    
    print(f"\n🎉 NETWORK CLUSTERING COMPLETE!")
    print(f"📁 Ready for integration with core skills intelligence")
    print(f"🏗️ Provides skill ecosystem context for strategic architecture") 