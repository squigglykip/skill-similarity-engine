#!/usr/bin/env python3
"""
Debug training feasibility to understand scoring distribution
"""

from src.skill_similarity_engine.models.clustering_analyzer import SkillsBundleClusterer
import pandas as pd

def debug_training_feasibility():
    print("🔍 Debugging training feasibility scoring...")
    
    clusterer = SkillsBundleClusterer()
    db_path = 'models/2025-Q3/business_context.sqlite'
    
    # Load and cluster skills
    skills_data = clusterer._load_skills_data(db_path)
    clustered_skills = clusterer._perform_skills_clustering(skills_data)
    
    # Look at a few clusters in detail
    unique_clusters = clustered_skills['cluster_id'].unique()
    print(f"📊 Found {len(unique_clusters)} clusters")
    
    for cluster_id in unique_clusters[:5]:  # Look at first 5 clusters
        if cluster_id == -1:  # Skip noise
            continue
            
        cluster_skills = clustered_skills[clustered_skills['cluster_id'] == cluster_id]
        
        print(f"\n🔍 Cluster {cluster_id} Analysis:")
        print(f"   Size: {len(cluster_skills)} skills")
        print(f"   Avg prevalence: {cluster_skills['prevalence_percent'].mean():.1f}%")
        print(f"   Avg jobs per skill: {cluster_skills['jobs_count'].mean():.1f}")
        
        # Calculate factors manually
        bundle_size = len(cluster_skills)
        avg_prevalence = cluster_skills['prevalence_percent'].mean()
        avg_jobs_per_skill = cluster_skills['jobs_count'].mean()
        category_purity = (cluster_skills['category'] == cluster_skills['category'].mode().iloc[0]).mean()
        
        # Size feasibility
        if bundle_size <= 5:
            size_feasibility = 1.0
        elif bundle_size <= 15:
            size_feasibility = 0.8
        elif bundle_size <= 30:
            size_feasibility = 0.6
        elif bundle_size <= 50:
            size_feasibility = 0.4
        else:
            size_feasibility = 0.2
            
        # Prevalence feasibility
        if avg_prevalence >= 40:
            prevalence_feasibility = 1.0
        elif avg_prevalence >= 20:
            prevalence_feasibility = 0.8
        elif avg_prevalence >= 10:
            prevalence_feasibility = 0.6
        elif avg_prevalence >= 5:
            prevalence_feasibility = 0.4
        else:
            prevalence_feasibility = 0.2
            
        # Specialization feasibility
        if avg_jobs_per_skill >= 100:
            specialization_feasibility = 1.0
        elif avg_jobs_per_skill >= 50:
            specialization_feasibility = 0.8
        elif avg_jobs_per_skill >= 20:
            specialization_feasibility = 0.6
        elif avg_jobs_per_skill >= 10:
            specialization_feasibility = 0.4
        else:
            specialization_feasibility = 0.2
            
        # Final score
        training_feasibility_score = (
            0.35 * size_feasibility +
            0.25 * category_purity +
            0.25 * prevalence_feasibility +
            0.15 * specialization_feasibility
        )
        
        print(f"   Factor scores:")
        print(f"     Size feasibility: {size_feasibility:.2f}")
        print(f"     Category purity: {category_purity:.2f}")
        print(f"     Prevalence feasibility: {prevalence_feasibility:.2f}")
        print(f"     Specialization feasibility: {specialization_feasibility:.2f}")
        print(f"   Final score: {training_feasibility_score:.3f}")
        
        # Assessment
        if training_feasibility_score >= 0.7:
            assessment = "high"
        elif training_feasibility_score >= 0.4:
            assessment = "medium"
        else:
            assessment = "low"
            
        print(f"   Assessment: {assessment}")

if __name__ == "__main__":
    debug_training_feasibility()
