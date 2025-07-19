#!/usr/bin/env python3
"""
Skills Intelligence Predictive Engine
=====================================

This module generates skills confidence scores for all job profile pairs (715 x 715 = 510,510 pairs)
by analyzing defining skills overlap, skill rarity weighting, and skill gap patterns.

Key Features:
1. Defining skills analysis with rarity-based weighting (rare=3x, uncommon=2x, common=1x)
2. Skill gap identification and bridgeability assessment
3. Gateway skills discovery for cross-functional transitions
4. Skills confidence scoring for cartesian product of all job profiles
5. Smart filtering to exclude low-confidence pairs (<10%)

Builds on:
- skill_enrichment_analysis.py (skill rarity categorization, growth trends)
- 03_role_typology_pathway_enhancement_enhanced.py (defining skills analysis)
- Existing asymmetric similarity calculations
"""

import pandas as pd
import numpy as np
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, jaccard_score
import warnings
import gc
import psutil
import os
from pathlib import Path
from datetime import datetime
from itertools import product
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict, Counter
import json
import time

warnings.filterwarnings('ignore')

# Set plotting style
plt.style.use('default')
sns.set_palette("husl")

# =============================================================================
# CONFIGURATION
# =============================================================================

# Database configuration - updated for real data scale
DATABASE_FILE = 'models/2025-Q3/workforce_intelligence.sqlite'

# Skills confidence scoring weights
SKILLS_CONFIDENCE_WEIGHTS = {
    'defining_skills_overlap': 0.40,       # Core defining skills match
    'total_skills_coverage': 0.20,         # Overall skill coverage
    'rarity_bonus': 0.15,                  # Bonus for rare skill matches
    'gateway_skills_bonus': 0.10,          # Bonus for cross-functional gateway skills
    'skill_gap_penalty': 0.15              # Penalty for critical skill gaps
}

# Skill rarity weighting configuration (from skill_enrichment_analysis.py)
SKILL_RARITY_WEIGHTS = {
    'rare': 3.0,        # <5% prevalence - highest weight
    'uncommon': 2.0,    # 5-20% prevalence - medium weight
    'common': 1.0,      # 20-50% prevalence - standard weight
    'universal': 0.5    # >50% prevalence - reduced weight
}

# Skill rarity thresholds
SKILL_RARITY_THRESHOLDS = {
    'rare': 5.0,        # <5% = rare skill
    'uncommon': 20.0,   # 5-20% = uncommon skill  
    'common': 50.0,     # 20-50% = common skill
    # >50% = universal skill
}

# Defining skills configuration
DEFINING_SKILLS_CONFIG = {
    'min_jobs_for_analysis': 1,        # Minimum jobs to analyze (full coverage)
    'top_n_defining': 5,               # Top N defining skills per role
    'min_skill_frequency': 2,          # Minimum frequency for skill analysis
    'defining_threshold': 0.1          # Threshold for considering skill as "defining"
}

# Gateway skills configuration  
GATEWAY_SKILLS_CONFIG = {
    'min_cross_function_jobs': 3,      # Minimum jobs across functions to be gateway
    'gateway_prevalence_threshold': 15, # Skills in 10-30% of roles can be gateways
    'max_gateway_prevalence': 40       # Too universal to be a gateway
}

# Confidence thresholds
CONFIDENCE_THRESHOLD = 15.0            # Minimum confidence for inclusion in final dataset
MIN_SKILLS_FOR_COMPARISON = 1         # Minimum skills to perform comparison

# Memory management
CHUNK_SIZE = 10000
MAX_MEMORY_MB = 8000

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_memory_usage():
    """Get current memory usage information"""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    return {
        'current_process_usage_mb': memory_info.rss / 1024 / 1024,
        'available_memory_mb': psutil.virtual_memory().available / 1024 / 1024
    }

def trigger_garbage_collection():
    """Trigger garbage collection to free memory"""
    gc.collect()

def print_section_header(title, description=""):
    """Print a formatted section header"""
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}")
    if description:
        print(f"{description}")
        print()

def print_memory_status():
    """Print current memory usage"""
    memory_usage = get_memory_usage()
    print(f"💾 Memory: {memory_usage['current_process_usage_mb']:.1f} MB")

def categorize_skill_rarity(prevalence_percentage):
    """Categorize skill rarity based on prevalence across job profiles"""
    if prevalence_percentage < SKILL_RARITY_THRESHOLDS['rare']:
        return 'rare'
    elif prevalence_percentage < SKILL_RARITY_THRESHOLDS['uncommon']:
        return 'uncommon'
    elif prevalence_percentage < SKILL_RARITY_THRESHOLDS['common']:
        return 'common'
    else:
        return 'universal'

# =============================================================================
# DATA LOADING AND PREPARATION
# =============================================================================

def load_database_connection():
    """Load database connection and verify tables"""
    print(f"🔗 Connecting to database: {DATABASE_FILE}")
    
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        print(f"✅ Successfully connected to database")
        return conn
    except sqlite3.OperationalError as e:
        raise FileNotFoundError(f"Could not connect to database: {DATABASE_FILE}. Error: {str(e)}")

def load_skills_data(conn):
    """Load skills taxonomy and job-skill mappings"""
    print("📚 Loading skills taxonomy and job mappings...")
    
    # Load skills taxonomy
    skills_df = pd.read_sql_query("SELECT * FROM skills", conn)
    print(f"✅ Loaded {len(skills_df):,} skills from taxonomy")
    
    # Load job-skill mappings
    job_skills_df = pd.read_sql_query("SELECT * FROM job_skills", conn)
    print(f"✅ Loaded {len(job_skills_df):,} job-skill relationships")
    
    # Load job architecture
    jobs_df = pd.read_sql_query("SELECT * FROM jobs", conn)
    print(f"✅ Loaded {len(jobs_df):,} job profiles")
    
    return skills_df, job_skills_df, jobs_df

def calculate_skill_prevalence_and_rarity(job_skills_df, jobs_df):
    """Calculate skill prevalence across job profiles and categorize rarity"""
    print("🔍 Calculating skill prevalence and rarity categorization...")
    
    total_jobs = len(jobs_df)
    
    # Calculate prevalence for each skill
    skill_prevalence = job_skills_df.groupby('Skill_ID').agg({
        'JobProfileID': 'nunique'
    }).reset_index()
    
    skill_prevalence['prevalence_count'] = skill_prevalence['JobProfileID']
    skill_prevalence['prevalence_percentage'] = (skill_prevalence['prevalence_count'] / total_jobs) * 100
    skill_prevalence['rarity_category'] = skill_prevalence['prevalence_percentage'].apply(categorize_skill_rarity)
    skill_prevalence['rarity_weight'] = skill_prevalence['rarity_category'].map(SKILL_RARITY_WEIGHTS)
    
    print(f"✅ Calculated prevalence for {len(skill_prevalence):,} unique skills")
    
    # Display rarity distribution
    rarity_dist = skill_prevalence['rarity_category'].value_counts()
    print(f"📊 Skill rarity distribution:")
    for category, count in rarity_dist.items():
        avg_prevalence = skill_prevalence[skill_prevalence['rarity_category'] == category]['prevalence_percentage'].mean()
        print(f"   → {category.capitalize()}: {count:,} skills (avg prevalence: {avg_prevalence:.2f}%)")
    
    return skill_prevalence

def identify_defining_skills_per_job(job_skills_df, skill_prevalence, jobs_df):
    """
    Identify defining skills for each job profile based on rarity and job-specific importance
    """
    print("🎯 Identifying defining skills per job profile...")
    
    defining_skills_per_job = {}
    
    # Merge job skills with rarity information
    job_skills_with_rarity = job_skills_df.merge(
        skill_prevalence[['Skill_ID', 'rarity_category', 'rarity_weight', 'prevalence_percentage']],
        on='Skill_ID',
        how='left'
    )
    
    for job_id in jobs_df['JobProfileID'].unique():
        job_skills = job_skills_with_rarity[job_skills_with_rarity['JobProfileID'] == job_id]
        
        if len(job_skills) == 0:
            defining_skills_per_job[job_id] = []
            continue
        
        # Calculate defining score: skill_weight * rarity_weight * (1 - prevalence_penalty)
        job_skills['prevalence_penalty'] = job_skills['prevalence_percentage'] / 100
        job_skills['defining_score'] = (
            job_skills['Skill_Weight'] * 
            job_skills['rarity_weight'] * 
            (1 - job_skills['prevalence_penalty'])
        )
        
        # Get top defining skills
        top_defining = job_skills.nlargest(
            DEFINING_SKILLS_CONFIG['top_n_defining'], 
            'defining_score'
        )
        
        defining_skills_list = []
        for _, skill_row in top_defining.iterrows():
            defining_skills_list.append({
                'skill_id': skill_row['Skill_ID'],
                'skill_weight': skill_row['Skill_Weight'],
                'rarity_category': skill_row['rarity_category'],
                'rarity_weight': skill_row['rarity_weight'],
                'prevalence_percentage': skill_row['prevalence_percentage'],
                'defining_score': skill_row['defining_score']
            })
        
        defining_skills_per_job[job_id] = defining_skills_list
    
    # Report statistics
    jobs_with_defining_skills = len([j for j in defining_skills_per_job.values() if len(j) > 0])
    avg_defining_skills = np.mean([len(j) for j in defining_skills_per_job.values()])
    
    print(f"✅ Identified defining skills for {jobs_with_defining_skills:,} job profiles")
    print(f"📊 Average defining skills per job: {avg_defining_skills:.2f}")
    
    return defining_skills_per_job

def detect_gateway_skills(skills_df, jobs_df, job_skills_df, min_functions=2, min_prevalence=0.05, max_prevalence=0.60):
    """
    Detect gateway skills that facilitate transitions between job functions.
    UPDATED CRITERIA based on debug analysis:
    - Reduced min_functions from 3 to 2 (more realistic for dataset)
    - Reduced min_prevalence from 15% to 5% (account for synthetic data sparsity)  
    - Increased max_prevalence from 40% to 60% (avoid excluding too many skills)
    """
    print(f"🔬 Detecting gateway skills with updated criteria:")
    print(f"   → min_functions: {min_functions}")
    print(f"   → min_prevalence: {min_prevalence:.1%}")
    print(f"   → max_prevalence: {max_prevalence:.1%}")
    
    # Calculate skill prevalence across functions
    skill_function_counts = (
        job_skills_df.merge(jobs_df[['Job Profile', 'Function']], on='Job Profile')
        .groupby('Skill ID')['Function']
        .nunique()
        .reset_index()
        .rename(columns={'Function': 'function_count'})
    )
    
    # Calculate overall prevalence
    skill_prevalence = (
        job_skills_df.groupby('Skill ID')['Job Profile']
        .nunique()
        .reset_index()
        .rename(columns={'Job Profile': 'job_count'})
    )
    skill_prevalence['prevalence'] = skill_prevalence['job_count'] / len(jobs_df)
    
    # Combine metrics
    gateway_analysis = skill_function_counts.merge(skill_prevalence, on='Skill ID')
    
    # Apply gateway criteria
    gateway_skills = gateway_analysis[
        (gateway_analysis['function_count'] >= min_functions) &
        (gateway_analysis['prevalence'] >= min_prevalence) &
        (gateway_analysis['prevalence'] <= max_prevalence)
    ]
    
    print(f"📊 Gateway skills found: {len(gateway_skills)}")
    if len(gateway_skills) > 0:
        print(f"   → Function count range: {gateway_skills['function_count'].min()}-{gateway_skills['function_count'].max()}")
        print(f"   → Prevalence range: {gateway_skills['prevalence'].min():.1%}-{gateway_skills['prevalence'].max():.1%}")
        
        # Show top gateway skills
        top_gateway = gateway_skills.nlargest(5, 'function_count')
        print(f"   → Top 5 gateway skills:")
        for _, skill in top_gateway.iterrows():
            print(f"     • {skill['Skill ID']}: {skill['function_count']} functions, {skill['prevalence']:.1%} prevalence")
    
    return set(gateway_skills['Skill ID'].tolist())

def calculate_simple_skills_confidence(source_skills, target_skills, skill_rarity_dict, gateway_skills_set, 
                                       source_job_name="Unknown", target_job_name="Unknown", verbose=False):
    """
    Skills confidence calculation optimized for real data patterns.
    
    Based on real data analysis showing:
    - 93% skills are "rare" (realistic for enterprise)
    - Good mobility score distribution (3.0-74.1 range)
    - Rich skill transition networks
    - Need for higher confidence thresholds
    """
    source_set = set(source_skills)
    target_set = set(target_skills)
    
    if not source_set or not target_set:
        return 0.0, {}
    
    # 1. Basic overlap (35% weight) - reduced slightly as real data has better differentiation
    overlap = source_set.intersection(target_set)
    overlap_score = len(overlap) / len(source_set) if source_set else 0
    
    # 2. Coverage (35% weight) - increased for real data
    coverage_score = len(overlap) / len(target_set) if target_set else 0
    
    # 3. Rarity bonus (20% weight) - adjusted for 93% rare skills in real data
    avg_rarity = 0  # Initialize avg_rarity
    if overlap and skill_rarity_dict:
        rarities = [skill_rarity_dict.get(skill, 0.5) for skill in overlap]
        avg_rarity = np.mean(rarities)
        
        # Adjusted rarity bonus for real data where 93% are rare
        # Focus on the truly exceptional rare skills (< 1% prevalence)
        if avg_rarity < 0.01:  # Extremely rare
            rarity_bonus = 50  # High bonus
        elif avg_rarity < 0.05:  # Rare
            rarity_bonus = 25  # Moderate bonus
        else:  # Common/universal
            rarity_bonus = 5   # Small bonus
    else:
        rarity_bonus = 0
    
    # 4. Gateway bonus (10% weight) - should work much better with real data
    gateway_overlap = overlap.intersection(gateway_skills_set) if gateway_skills_set else set()
    gateway_bonus = min(30, len(gateway_overlap) * 15)  # 15% per gateway skill, capped at 30%
    
    # Final weighted score - adjusted weights for real data
    components = {
        'overlap': overlap_score * 35,
        'coverage': coverage_score * 35,
        'rarity_bonus': rarity_bonus * 0.20,
        'gateway_bonus': gateway_bonus * 0.10
    }
    
    final_score = sum(components.values())
    final_score = min(100, max(0, final_score))
    
    # Create detailed breakdown
    breakdown = {
        'source_skills_count': len(source_set),
        'target_skills_count': len(target_set),
        'overlap_count': len(overlap),
        'overlap_ratio': overlap_score,
        'coverage_ratio': coverage_score,
        'avg_rarity': avg_rarity if overlap and skill_rarity_dict else 0,
        'gateway_skills_count': len(gateway_overlap),
        'components': components,
        'final_score': final_score
    }
    
    if verbose:
        print(f"  📊 {source_job_name} → {target_job_name}")
        print(f"     Skills: {len(source_set)} → {len(target_set)}, Overlap: {len(overlap)}")
        print(f"     Overlap: {overlap_score:.3f} ({components['overlap']:.1f}pts)")
        print(f"     Coverage: {coverage_score:.3f} ({components['coverage']:.1f}pts)")
        print(f"     Rarity: {avg_rarity:.3f} avg ({components['rarity_bonus']:.1f}pts)")
        print(f"     Gateway: {len(gateway_overlap)} skills ({components['gateway_bonus']:.1f}pts)")
        print(f"     Total: {final_score:.1f}%")
    
    return final_score, breakdown

def enhanced_gateway_detection(job_skills_df, jobs_df, min_functions=3, min_prevalence=0.02):
    """
    Gateway skills detection optimized for real data patterns.
    
    Real data showed successful skill mobility analysis, so using slightly
    more aggressive criteria than synthetic data adjustments.
    """
    print(f"🔬 Enhanced gateway detection for real data: ≥{min_functions} functions, ≥{min_prevalence:.1%} prevalence")
    
    # Calculate skill prevalence across functions  
    skill_function_counts = (
        job_skills_df.merge(jobs_df[['JobProfileID', 'JobFunction']], on='JobProfileID')
        .groupby('Skill_ID')['JobFunction']
        .nunique()
        .reset_index()
        .rename(columns={'JobFunction': 'function_count'})
    )
    
    # Calculate overall prevalence
    total_jobs = len(jobs_df)
    skill_job_counts = (
        job_skills_df.groupby('Skill_ID')['JobProfileID']
        .nunique()
        .reset_index()
        .rename(columns={'JobProfileID': 'job_count'})
    )
    skill_job_counts['prevalence'] = skill_job_counts['job_count'] / total_jobs
    
    # Combine and filter - using criteria that should work well with real data
    gateway_analysis = skill_function_counts.merge(skill_job_counts, on='Skill_ID')
    gateway_skills = gateway_analysis[
        (gateway_analysis['function_count'] >= min_functions) &
        (gateway_analysis['prevalence'] >= min_prevalence) &
        (gateway_analysis['prevalence'] <= 0.40)  # Upper bound to exclude universal skills
    ]
    
    print(f"📊 Found {len(gateway_skills)} gateway skills (real data should have many more than synthetic)")
    if len(gateway_skills) > 0:
        print(f"   → Function range: {gateway_skills['function_count'].min()}-{gateway_skills['function_count'].max()}")
        print(f"   → Prevalence range: {gateway_skills['prevalence'].min():.1%}-{gateway_skills['prevalence'].max():.1%}")
        
        # Show top gateway skills
        top_gateway = gateway_skills.nlargest(5, 'function_count')
        print(f"   → Top 5 gateway skills:")
        for _, skill in top_gateway.iterrows():
            print(f"     • Skill {skill['Skill_ID']}: {skill['function_count']} functions, {skill['prevalence']:.1%} prevalence")
    
    return set(gateway_skills['Skill_ID'].tolist())

# =============================================================================
# CARTESIAN PRODUCT GENERATION
# =============================================================================

def prepare_job_skills_data(job_skills_df, skill_prevalence):
    """Prepare efficient lookup structures for skills analysis"""
    print("⚙️ Preparing job skills lookup structures...")
    
    # Create job skills dictionary (all skills per job)
    job_skills_dict = {}
    for job_id in job_skills_df['JobProfileID'].unique():
        job_skills = job_skills_df[job_skills_df['JobProfileID'] == job_id]['Skill_ID'].tolist()
        job_skills_dict[job_id] = job_skills
    
    # Create skill prevalence dictionary
    skill_prevalence_dict = skill_prevalence.set_index('Skill_ID').to_dict('index')
    
    print(f"✅ Prepared lookup structures for {len(job_skills_dict):,} jobs")
    
    return job_skills_dict, skill_prevalence_dict

def generate_cartesian_skills_analysis(jobs_df, defining_skills_per_job, job_skills_dict, 
                                       skill_prevalence_dict, gateway_skills_set, chunk_size=CHUNK_SIZE):
    """
    Generate skills confidence scores for all job profile pairs (715 x 715)
    Uses chunked processing to manage memory efficiently
    """
    print_section_header("CARTESIAN PRODUCT SKILLS ANALYSIS")
    print(f"Generating skills confidence scores for all job profile pairs...")
    
    # Get all unique job profile IDs
    all_job_ids = jobs_df['JobProfileID'].unique().tolist()
    total_pairs = len(all_job_ids) ** 2
    
    print(f"📊 Processing {len(all_job_ids):,} job profiles")
    print(f"📊 Total pairs to analyse: {total_pairs:,}")
    print(f"💾 Processing in chunks of {chunk_size:,} pairs")
    
    # Initialize results storage
    results = []
    processed_pairs = 0
    high_confidence_pairs = 0
    
    # Generate all possible pairs in chunks
    all_pairs = list(product(all_job_ids, all_job_ids))
    
    for i in range(0, len(all_pairs), chunk_size):
        chunk_pairs = all_pairs[i:i + chunk_size]
        chunk_results = []
        
        print(f"   → Processing chunk {i // chunk_size + 1}/{(len(all_pairs) + chunk_size - 1) // chunk_size} ({len(chunk_pairs):,} pairs)")
        
        for from_job_id, to_job_id in chunk_pairs:
            # Calculate skills confidence score
            # The original code used calculate_skills_confidence_score, which called calculate_defining_skills_overlap,
            # calculate_total_skills_coverage, calculate_gateway_skills_bonus, and calculate_skill_gap_penalty.
            # The new calculate_skills_confidence_enhanced function handles these components.
            # We need to pass the relevant data to the new function.
            
            # Get job names for explanation
            from_job_name = jobs_df[jobs_df['JobProfileID'] == from_job_id]['JobProfile'].iloc[0]
            to_job_name = jobs_df[jobs_df['JobProfileID'] == to_job_id]['JobProfile'].iloc[0]
            
            # Get defining skills for both jobs
            from_job_skills = defining_skills_per_job.get(from_job_id, [])
            to_job_skills = defining_skills_per_job.get(to_job_id, [])
            
            # Get skill rarity for both jobs
            from_skill_rarity = {s['skill_id']: s['rarity_weight'] for s in from_job_skills}
            to_skill_rarity = {s['skill_id']: s['rarity_weight'] for s in to_job_skills}
            
            # Call the enhanced confidence calculation function
            confidence_score, breakdown = calculate_simple_skills_confidence(
                from_job_skills, to_job_skills, from_skill_rarity, gateway_skills_set,
                source_job_name=from_job_name, target_job_name=to_job_name, verbose=False
            )
            
            # Only keep pairs above confidence threshold
            if confidence_score >= CONFIDENCE_THRESHOLD:
                chunk_results.append({
                    'from_job_id': from_job_id,
                    'to_job_id': to_job_id,
                    'skills_confidence': confidence_score,
                    'defining_skills_overlap': "N/A", # No longer calculated here
                    'total_skills_coverage': "N/A", # No longer calculated here
                    'rarity_bonus': "N/A", # No longer calculated here
                    'gateway_skills_bonus': "N/A", # No longer calculated here
                    'skill_gap_penalty': "N/A", # No longer calculated here
                    'overlapping_defining_skills': "N/A", # No longer calculated here
                    'overlapping_total_skills': "N/A", # No longer calculated here
                    'rare_skills_overlap': "N/A", # No longer calculated here
                    'is_cross_functional': "N/A", # No longer calculated here
                    'gateway_skills_present': "N/A", # No longer calculated here
                    'missing_critical_skills': "N/A", # No longer calculated here
                    'breakdown': breakdown # Store breakdown
                })
                high_confidence_pairs += 1
            
            processed_pairs += 1
        
        # Add chunk results to main results
        results.extend(chunk_results)
        
        # Memory management
        trigger_garbage_collection()
        print_memory_status()
    
    # Convert to DataFrame
    skills_analysis_df = pd.DataFrame(results)
    
    print(f"\n✅ Cartesian product analysis complete!")
    print(f"📊 Total pairs processed: {processed_pairs:,}")
    print(f"📊 High confidence pairs (≥{CONFIDENCE_THRESHOLD}%): {high_confidence_pairs:,}")
    print(f"📊 Retention rate: {(high_confidence_pairs / processed_pairs * 100):.2f}%")
    
    return skills_analysis_df

# =============================================================================
# COMPREHENSIVE ANALYSIS AND INSIGHTS
# =============================================================================

def analyze_skills_patterns(skills_analysis_df, jobs_df, skills_df):
    """Generate comprehensive insights from the skills analysis results"""
    print_section_header("COMPREHENSIVE SKILLS PATTERN ANALYSIS")
    
    if skills_analysis_df.empty:
        print("⚠️ No high-confidence skills patterns found")
        return
    
    # Merge with job information for analysis
    analysis_with_jobs = skills_analysis_df.merge(
        jobs_df[['JobProfileID', 'JobProfile', 'JobFunction', 'JobSubFunction', 'ManagementLevel']],
        left_on='from_job_id',
        right_on='JobProfileID',
        how='left',
        suffixes=('', '_from')
    ).merge(
        jobs_df[['JobProfileID', 'JobProfile', 'JobFunction', 'JobSubFunction', 'ManagementLevel']],
        left_on='to_job_id',
        right_on='JobProfileID',
        how='left',
        suffixes=('_from', '_to')
    )
    
    print("🔍 TOP SKILLS CONFIDENCE SCORES WITH BREAKDOWN:")
    print("-" * 170)
    print(f"{'From → To':<85} {'Total':<8} {'Defining':<10} {'Coverage':<9} {'Rarity':<8} {'Gateway':<8} {'Gap Pen':<8} {'Rare Overlap':<10}")
    print("-" * 170)
    
    top_skills = skills_analysis_df.nlargest(20, 'skills_confidence')
    top_skills_with_jobs = top_skills.merge(
        jobs_df[['JobProfileID', 'JobProfile']],
        left_on='from_job_id',
        right_on='JobProfileID',
        how='left'
    ).merge(
        jobs_df[['JobProfileID', 'JobProfile']],
        left_on='to_job_id',
        right_on='JobProfileID',
        how='left',
        suffixes=('_from', '_to')
    )
    
    for _, row in top_skills_with_jobs.iterrows():
        from_job = row.get('JobProfile_from', row['from_job_id'])[:40] if pd.notna(row.get('JobProfile_from')) else row['from_job_id']
        to_job = row.get('JobProfile_to', row['to_job_id'])[:40] if pd.notna(row.get('JobProfile_to')) else row['to_job_id']
        from_to = f"{from_job} → {to_job}"
        print(f"{from_to:<85} {row['skills_confidence']:.1f}%   {row['defining_skills_overlap']:.3f}     {row['total_skills_coverage']:.3f}    {row['rarity_bonus']:.3f}   {row['gateway_skills_bonus']:.3f}   {row['skill_gap_penalty']:.3f}   {row['rare_skills_overlap']:<10}")
    
    print(f"\n📊 DETAILED CONFIDENCE COMPONENT ANALYSIS:")
    print(f"   → Mean confidence: {skills_analysis_df['skills_confidence'].mean():.2f}%")
    print(f"   → Median confidence: {skills_analysis_df['skills_confidence'].median():.2f}%")
    print(f"   → 90th percentile: {skills_analysis_df['skills_confidence'].quantile(0.9):.2f}%")
    print(f"   → 10th percentile: {skills_analysis_df['skills_confidence'].quantile(0.1):.2f}%")
    print(f"   → Standard deviation: {skills_analysis_df['skills_confidence'].std():.2f}%")
    
    # Component analysis
    print(f"\n🔬 COMPONENT CONTRIBUTION ANALYSIS:")
    components = {
        'defining_skills_overlap': SKILLS_CONFIDENCE_WEIGHTS['defining_skills_overlap'],
        'total_skills_coverage': SKILLS_CONFIDENCE_WEIGHTS['total_skills_coverage'],
        'rarity_bonus': SKILLS_CONFIDENCE_WEIGHTS['rarity_bonus'],
        'gateway_skills_bonus': SKILLS_CONFIDENCE_WEIGHTS['gateway_skills_bonus'],
        'skill_gap_penalty': SKILLS_CONFIDENCE_WEIGHTS['skill_gap_penalty']
    }
    
    for component, weight in components.items():
        mean_val = skills_analysis_df[component].mean()
        weighted_contribution = mean_val * weight * 100
        print(f"   → {component:<25}: Mean={mean_val:.3f}, Weight={weight:.2f}, Contribution={weighted_contribution:.2f}%")
    
    # Distribution analysis
    print(f"\n📈 CONFIDENCE SCORE DISTRIBUTION:")
    bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    confidence_dist = pd.cut(skills_analysis_df['skills_confidence'], bins=bins).value_counts().sort_index()
    for interval, count in confidence_dist.items():
        percentage = (count / len(skills_analysis_df)) * 100
        print(f"   → {interval}: {count:,} pairs ({percentage:.2f}%)")
    
    # Defining skills analysis
    print(f"\n📚 DEFINING SKILLS OVERLAP ANALYSIS:")
    with_defining_overlap = skills_analysis_df[skills_analysis_df['overlapping_defining_skills'] > 0]
    print(f"   → Pairs with defining skills overlap: {len(with_defining_overlap):,} ({len(with_defining_overlap)/len(skills_analysis_df)*100:.2f}%)")
    
    if len(with_defining_overlap) > 0:
        print(f"   → Mean defining skills overlap: {with_defining_overlap['defining_skills_overlap'].mean():.4f}")
        print(f"   → Mean overlapping defining skills count: {with_defining_overlap['overlapping_defining_skills'].mean():.2f}")
        print(f"   → Max overlapping defining skills: {with_defining_overlap['overlapping_defining_skills'].max()}")
    
    # Rare skills analysis
    print(f"\n💎 RARE SKILLS ANALYSIS:")
    with_rare_overlap = skills_analysis_df[skills_analysis_df['rare_skills_overlap'] > 0]
    print(f"   → Pairs with rare skills overlap: {len(with_rare_overlap):,} ({len(with_rare_overlap)/len(skills_analysis_df)*100:.2f}%)")
    
    if len(with_rare_overlap) > 0:
        print(f"   → Mean rare skills overlap: {with_rare_overlap['rare_skills_overlap'].mean():.2f}")
        print(f"   → Max rare skills overlap: {with_rare_overlap['rare_skills_overlap'].max()}")
        print(f"   → Mean confidence with rare overlap: {with_rare_overlap['skills_confidence'].mean():.2f}%")
    
    # Gateway skills analysis
    print(f"\n🌉 GATEWAY SKILLS ANALYSIS:")
    cross_functional = skills_analysis_df[skills_analysis_df['is_cross_functional'] == True]
    same_functional = skills_analysis_df[skills_analysis_df['is_cross_functional'] == False]
    
    print(f"   → Same function transitions: {len(same_functional):,} ({len(same_functional)/len(skills_analysis_df)*100:.2f}%)")
    print(f"   → Cross-functional transitions: {len(cross_functional):,} ({len(cross_functional)/len(skills_analysis_df)*100:.2f}%)")
    
    if len(cross_functional) > 0:
        with_gateway_skills = cross_functional[cross_functional['gateway_skills_present'] > 0]
        print(f"   → Cross-functional with gateway skills: {len(with_gateway_skills):,} ({len(with_gateway_skills)/len(cross_functional)*100:.2f}%)")
        print(f"   → Mean gateway skills present: {cross_functional['gateway_skills_present'].mean():.2f}")
        print(f"   → Mean confidence (same function): {same_functional['skills_confidence'].mean():.2f}%")
        print(f"   → Mean confidence (cross-functional): {cross_functional['skills_confidence'].mean():.2f}%")
    
    # Skill gaps analysis
    print(f"\n⚠️  SKILL GAPS ANALYSIS:")
    with_gaps = skills_analysis_df[skills_analysis_df['missing_critical_skills'] > 0]
    print(f"   → Pairs with skill gaps: {len(with_gaps):,} ({len(with_gaps)/len(skills_analysis_df)*100:.2f}%)")
    
    if len(with_gaps) > 0:
        print(f"   → Mean skill gap penalty: {with_gaps['skill_gap_penalty'].mean():.3f}")
        print(f"   → Mean missing critical skills: {with_gaps['missing_critical_skills'].mean():.2f}")
        print(f"   → Max missing critical skills: {with_gaps['missing_critical_skills'].max()}")
    
    # Quality assessment
    print(f"\n🎯 QUALITY ASSESSMENT:")
    
    retention_rate = len(skills_analysis_df) / (715 * 715) * 100
    print(f"   → Retention rate: {retention_rate:.2f}%")
    
    # Check for reasonable distributions
    defining_overlap_variance = skills_analysis_df['defining_skills_overlap'].var()
    coverage_variance = skills_analysis_df['total_skills_coverage'].var()
    
    print(f"   → Defining overlap variance: {defining_overlap_variance:.6f}")
    print(f"   → Coverage variance: {coverage_variance:.6f}")
    
    if retention_rate > 90:
        print(f"   ⚠️  HIGH RETENTION RATE: {retention_rate:.2f}% (may need higher threshold)")
    
    if defining_overlap_variance < 0.01:
        print(f"   ⚠️  LOW VARIANCE: Defining overlap scores may be too uniform")
    
    print(f"\n💡 SKILLS INTELLIGENCE INSIGHTS:")
    print(f"   → Skills-based pathways show {'higher' if len(with_rare_overlap) > len(skills_analysis_df)*0.1 else 'lower'} rare skill connectivity")
    print(f"   → Cross-functional transitions {'are' if len(cross_functional) > len(same_functional) else 'are not'} dominant")
    print(f"   → Gateway skills {'effectively' if len(cross_functional) > 0 and cross_functional['gateway_skills_present'].mean() > 1 else 'minimally'} support transitions")
    print(f"   → Skill gaps {'significantly' if with_gaps['skill_gap_penalty'].mean() > 0.3 else 'moderately'} impact pathway viability")

def save_skills_analysis_results(skills_analysis_df, output_path="skills_confidence_analysis.csv"):
    """Save the skills analysis results to CSV"""
    print(f"\n💾 Saving skills analysis results to {output_path}")
    skills_analysis_df.to_csv(output_path, index=False)
    print(f"✅ Saved {len(skills_analysis_df):,} skills confidence scores")

# =============================================================================
# MAIN EXECUTION FUNCTION
# =============================================================================

def main():
    """
    Main execution function for skills intelligence predictive analysis
    UPDATED: Fixed column references and enhanced gateway criteria based on debug findings
    """
    
    print("="*80)
    print("SKILLS INTELLIGENCE PREDICTIVE ANALYSIS")
    print("="*80)
    print("Generating skills confidence scores for career pathway recommendations")
    print("Enhanced with debug findings: adjusted gateway criteria and scoring logic")
    
    # Connect to database
    conn = sqlite3.connect(DATABASE_FILE)
    print(f"🔗 Connected to database: {DATABASE_FILE}")
    
    try:
        # 1. Load data with corrected column names
        print("\n" + "="*60)
        print("DATA LOADING & PREPARATION")
        print("="*60)
        
        jobs_df = pd.read_sql_query("SELECT * FROM jobs", conn)
        job_skills_df = pd.read_sql_query("SELECT * FROM job_skills", conn) 
        skills_df = pd.read_sql_query("SELECT * FROM skills", conn)
        
        print(f"📊 Loaded {len(jobs_df):,} job profiles")
        print(f"📊 Loaded {len(job_skills_df):,} job-skill relationships")
        print(f"📊 Loaded {len(skills_df):,} unique skills")
        
        # Debug: Check actual column names
        print(f"\n🔍 Jobs DataFrame columns: {list(jobs_df.columns)}")
        print(f"🔍 Job-Skills DataFrame columns: {list(job_skills_df.columns)}")
        
        # 2. Calculate skill prevalence and rarity
        skill_prevalence = calculate_skill_prevalence_and_rarity(job_skills_df, jobs_df)
        
        # 3. Identify defining skills for each job
        defining_skills_per_job = identify_defining_skills_per_job(job_skills_df, skill_prevalence, jobs_df)
        
        # 4. Detect gateway skills with updated criteria (from debug analysis)
        print("\n🌉 Detecting gateway skills with enhanced criteria...")
        gateway_skills_set = enhanced_gateway_detection(
            job_skills_df, jobs_df, 
            min_functions=3,      # Reduced from 3 (more realistic)
            min_prevalence=0.02   # Reduced from 0.15 (account for synthetic data)
        )
        
        # 5. Create skill rarity lookup for enhanced scoring
        skill_rarity_lookup = {}
        for _, row in skill_prevalence.iterrows():
            skill_id = row['Skill_ID']
            prevalence = row['prevalence_percentage'] / 100
            skill_rarity_lookup[skill_id] = prevalence
        
        # 6. Prepare job skills lookup
        job_skills_dict = {}
        for _, row in job_skills_df.iterrows():
            job_id = row['JobProfileID']
            skill_id = row['Skill_ID']
            if job_id not in job_skills_dict:
                job_skills_dict[job_id] = []
            job_skills_dict[job_id].append(skill_id)
        
        # 7. Generate cartesian product analysis with enhanced scoring
        print("\n" + "="*60)
        print("CARTESIAN PRODUCT SKILLS ANALYSIS")
        print("="*60)
        
        results_data = []
        job_ids = jobs_df['JobProfileID'].unique()
        total_pairs = len(job_ids) ** 2
        chunk_size = 10000
        
        print(f"🔢 Processing {total_pairs:,} job profile pairs...")
        print(f"📦 Using chunk size: {chunk_size:,}")
        
        chunk_count = 0
        high_confidence_pairs = 0
        
        # Generate all pairs and process in chunks
        all_pairs = list(product(job_ids, job_ids))
        
        for i in range(0, len(all_pairs), chunk_size):
            chunk_pairs = all_pairs[i:i + chunk_size]
            chunk_count += 1
            
            print(f"   → Processing chunk {chunk_count} ({len(chunk_pairs):,} pairs)")
            
            for from_job_id, to_job_id in chunk_pairs:
                # Get job names for better explanation
                from_job_name = jobs_df[jobs_df['JobProfileID'] == from_job_id]['JobProfile'].iloc[0]
                to_job_name = jobs_df[jobs_df['JobProfileID'] == to_job_id]['JobProfile'].iloc[0]
                
                # Get skills for both jobs
                from_job_skills = job_skills_dict.get(from_job_id, [])
                to_job_skills = job_skills_dict.get(to_job_id, [])
                
                # Calculate enhanced skills confidence (no verbose output during main run)
                confidence_score, breakdown = calculate_simple_skills_confidence(
                    from_job_skills, to_job_skills, skill_rarity_lookup, gateway_skills_set,
                    source_job_name=from_job_name, target_job_name=to_job_name, verbose=False
                )
                
                # Filter and store high-confidence pairs
                if confidence_score >= CONFIDENCE_THRESHOLD:
                    results_data.append({
                        'from_job_id': from_job_id,
                        'to_job_id': to_job_id,
                        'from_job_name': from_job_name,
                        'to_job_name': to_job_name,
                        'skills_confidence': confidence_score,
                        'explanation': "N/A", # No longer calculated here
                        'breakdown': breakdown # Store breakdown
                    })
                    high_confidence_pairs += 1
            
            # Progress reporting
            processed_pairs = min(i + chunk_size, len(all_pairs))
            if chunk_count % 10 == 0:
                print(f"⏳ Processed {processed_pairs:,}/{total_pairs:,} pairs "
                      f"({100 * processed_pairs / total_pairs:.1f}%) - "
                      f"High confidence: {high_confidence_pairs:,}")
        
        # 8. Create results DataFrame and summary
        skills_analysis_df = pd.DataFrame(results_data)
        
        print(f"\n✅ SKILLS INTELLIGENCE ANALYSIS COMPLETE")
        print(f"📊 High-confidence pairs (≥{CONFIDENCE_THRESHOLD}%): {len(skills_analysis_df):,}")
        print(f"📊 Average confidence score: {skills_analysis_df['skills_confidence'].mean():.1f}%")
        print(f"📊 Confidence score range: {skills_analysis_df['skills_confidence'].min():.1f}% - {skills_analysis_df['skills_confidence'].max():.1f}%")
        
        # === COMPREHENSIVE DIAGNOSTIC ANALYSIS ===
        print(f"\n" + "="*80)
        print("COMPREHENSIVE DIAGNOSTIC ANALYSIS")
        print("="*80)
        
        # 1. Score Distribution Analysis
        print(f"\n📈 CONFIDENCE SCORE DISTRIBUTION:")
        bins = [15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80]
        score_dist = pd.cut(skills_analysis_df['skills_confidence'], bins=bins, include_lowest=True).value_counts().sort_index()
        for interval, count in score_dist.items():
            percentage = (count / len(skills_analysis_df)) * 100
            print(f"   → {interval}: {count:,} pairs ({percentage:.1f}%)")
        
        # 2. Component Analysis
        print(f"\n🔬 COMPONENT CONTRIBUTION ANALYSIS:")
        sample_breakdowns = [r['breakdown'] for r in results_data[:1000] if 'breakdown' in r]  # Sample for analysis
        
        if sample_breakdowns:
            overlap_scores = [b['components']['overlap'] for b in sample_breakdowns]
            coverage_scores = [b['components']['coverage'] for b in sample_breakdowns]
            rarity_scores = [b['components']['rarity_bonus'] for b in sample_breakdowns]
            gateway_scores = [b['components']['gateway_bonus'] for b in sample_breakdowns]
            
            print(f"   → Overlap Component (35% weight):")
            print(f"     • Mean: {np.mean(overlap_scores):.2f} pts, Std: {np.std(overlap_scores):.2f}")
            print(f"     • Range: {np.min(overlap_scores):.1f} - {np.max(overlap_scores):.1f} pts")
            
            print(f"   → Coverage Component (35% weight):")
            print(f"     • Mean: {np.mean(coverage_scores):.2f} pts, Std: {np.std(coverage_scores):.2f}")
            print(f"     • Range: {np.min(coverage_scores):.1f} - {np.max(coverage_scores):.1f} pts")
            
            print(f"   → Rarity Bonus (20% of bonus):")
            print(f"     • Mean: {np.mean(rarity_scores):.2f} pts, Std: {np.std(rarity_scores):.2f}")
            print(f"     • Range: {np.min(rarity_scores):.1f} - {np.max(rarity_scores):.1f} pts")
            print(f"     • Non-zero rarity bonuses: {sum(1 for r in rarity_scores if r > 0)} of {len(rarity_scores)}")
            
            print(f"   → Gateway Bonus (10% of bonus):")
            print(f"     • Mean: {np.mean(gateway_scores):.2f} pts, Std: {np.std(gateway_scores):.2f}")
            print(f"     • Range: {np.min(gateway_scores):.1f} - {np.max(gateway_scores):.1f} pts")
            print(f"     • Pairs with gateway skills: {sum(1 for b in sample_breakdowns if b['gateway_skills_count'] > 0)}")
        
        # 3. Skills Overlap Patterns
        print(f"\n📚 SKILLS OVERLAP PATTERN ANALYSIS:")
        if sample_breakdowns:
            overlap_ratios = [b['overlap_ratio'] for b in sample_breakdowns]
            coverage_ratios = [b['coverage_ratio'] for b in sample_breakdowns]
            skill_counts_source = [b['source_skills_count'] for b in sample_breakdowns]
            skill_counts_target = [b['target_skills_count'] for b in sample_breakdowns]
            
            print(f"   → Overlap Ratios (skills from source found in target):")
            print(f"     • Mean: {np.mean(overlap_ratios):.3f}, Median: {np.median(overlap_ratios):.3f}")
            print(f"     • Perfect overlap (1.0): {sum(1 for r in overlap_ratios if r >= 0.99)} pairs")
            print(f"     • High overlap (>0.8): {sum(1 for r in overlap_ratios if r > 0.8)} pairs")
            print(f"     • Low overlap (<0.3): {sum(1 for r in overlap_ratios if r < 0.3)} pairs")
            
            print(f"   → Coverage Ratios (target skills covered by source):")
            print(f"     • Mean: {np.mean(coverage_ratios):.3f}, Median: {np.median(coverage_ratios):.3f}")
            print(f"     • Perfect coverage (1.0): {sum(1 for r in coverage_ratios if r >= 0.99)} pairs")
            
            print(f"   → Skills per Job Profile:")
            print(f"     • Source mean: {np.mean(skill_counts_source):.1f}, range: {min(skill_counts_source)}-{max(skill_counts_source)}")
            print(f"     • Target mean: {np.mean(skill_counts_target):.1f}, range: {min(skill_counts_target)}-{max(skill_counts_target)}")
        
        # 4. Rarity Analysis
        print(f"\n💎 RARITY PATTERN ANALYSIS:")
        if sample_breakdowns:
            avg_rarities = [b['avg_rarity'] for b in sample_breakdowns if b['avg_rarity'] > 0]
            
            print(f"   → Average Rarity Distribution (for overlapping skills):")
            print(f"     • Mean rarity: {np.mean(avg_rarities):.4f}")
            print(f"     • Extremely rare (<0.01): {sum(1 for r in avg_rarities if r < 0.01)}")
            print(f"     • Rare (<0.05): {sum(1 for r in avg_rarities if r < 0.05)}")
            print(f"     • Common (≥0.05): {sum(1 for r in avg_rarities if r >= 0.05)}")
        
        # 5. Quality Assessment
        print(f"\n🎯 QUALITY ASSESSMENT:")
        retention_rate = len(skills_analysis_df) / total_pairs * 100
        print(f"   → Retention Rate: {retention_rate:.1f}% ({len(skills_analysis_df):,} of {total_pairs:,} pairs)")
        
        score_variance = skills_analysis_df['skills_confidence'].var()
        print(f"   → Score Variance: {score_variance:.2f}")
        
        if retention_rate > 90:
            print(f"   ⚠️  Very high retention rate may indicate threshold too low")
        elif retention_rate < 10:
            print(f"   ⚠️  Very low retention rate may indicate threshold too high")
        else:
            print(f"   ✅ Retention rate appears reasonable")
        
        if float(score_variance) < 10:
            print(f"   ⚠️  Low score variance may indicate insufficient differentiation")
        else:
            print(f"   ✅ Good score variance indicates meaningful differentiation")
        
        # Show top pathway recommendations with details
        print(f"\n🔝 TOP 10 PATHWAY RECOMMENDATIONS WITH COMPONENT BREAKDOWN:")
        top_pathways = skills_analysis_df.nlargest(10, 'skills_confidence')
        for i, (_, pathway) in enumerate(top_pathways.iterrows(), 1):
            print(f"   {i}. {pathway['from_job_name']} → {pathway['to_job_name']}")
            print(f"      Skills Confidence: {pathway['skills_confidence']:.1f}%")
            if 'breakdown' in pathway and pathway['breakdown']:
                b = pathway['breakdown']
                print(f"      Components: Overlap={b['components']['overlap']:.1f}, "
                      f"Coverage={b['components']['coverage']:.1f}, "
                      f"Rarity={b['components']['rarity_bonus']:.1f}, "
                      f"Gateway={b['components']['gateway_bonus']:.1f}")
                print(f"      Skills: {b['source_skills_count']}→{b['target_skills_count']}, "
                      f"Overlap: {b['overlap_count']}, Gateway: {b['gateway_skills_count']}")
            print()
        
        # === DETAILED COMPONENT EXAMPLES TABLE ===
        print(f"\n" + "="*120)
        print("DETAILED COMPONENT BREAKDOWN EXAMPLES")
        print("="*120)
        
        # Select representative examples at different score levels
        high_examples = skills_analysis_df[skills_analysis_df['skills_confidence'] >= 60].head(3)
        medium_examples = skills_analysis_df[
            (skills_analysis_df['skills_confidence'] >= 35) & 
            (skills_analysis_df['skills_confidence'] < 50)
        ].head(3)
        low_examples = skills_analysis_df[
            (skills_analysis_df['skills_confidence'] >= 15) & 
            (skills_analysis_df['skills_confidence'] < 25)
        ].head(3)
        
        print(f"\n📊 HIGH CONFIDENCE EXAMPLES (≥60%):")
        print("-" * 120)
        print(f"{'From → To':<50} {'Total':<7} {'Overlap':<8} {'Coverage':<9} {'Rarity':<7} {'Gateway':<8} {'Skills':<15}")
        print("-" * 120)
        
        for _, row in high_examples.iterrows():
            if 'breakdown' in row and row['breakdown']:
                b = row['breakdown']
                from_to = f"{row['from_job_name'][:22]} → {row['to_job_name'][:22]}"
                print(f"{from_to:<50} {row['skills_confidence']:.1f}%   "
                      f"{b['components']['overlap']:.1f}pts   "
                      f"{b['components']['coverage']:.1f}pts    "
                      f"{b['components']['rarity_bonus']:.1f}pts  "
                      f"{b['components']['gateway_bonus']:.1f}pts   "
                      f"{b['source_skills_count']}→{b['target_skills_count']} ({b['overlap_count']} overlap)")
        
        print(f"\n📊 MEDIUM CONFIDENCE EXAMPLES (35-50%):")
        print("-" * 120)
        print(f"{'From → To':<50} {'Total':<7} {'Overlap':<8} {'Coverage':<9} {'Rarity':<7} {'Gateway':<8} {'Skills':<15}")
        print("-" * 120)
        
        for _, row in medium_examples.iterrows():
            if 'breakdown' in row and row['breakdown']:
                b = row['breakdown']
                from_to = f"{row['from_job_name'][:22]} → {row['to_job_name'][:22]}"
                print(f"{from_to:<50} {row['skills_confidence']:.1f}%   "
                      f"{b['components']['overlap']:.1f}pts   "
                      f"{b['components']['coverage']:.1f}pts    "
                      f"{b['components']['rarity_bonus']:.1f}pts  "
                      f"{b['components']['gateway_bonus']:.1f}pts   "
                      f"{b['source_skills_count']}→{b['target_skills_count']} ({b['overlap_count']} overlap)")
        
        print(f"\n📊 LOWER CONFIDENCE EXAMPLES (15-25%):")
        print("-" * 120)
        print(f"{'From → To':<50} {'Total':<7} {'Overlap':<8} {'Coverage':<9} {'Rarity':<7} {'Gateway':<8} {'Skills':<15}")
        print("-" * 120)
        
        for _, row in low_examples.iterrows():
            if 'breakdown' in row and row['breakdown']:
                b = row['breakdown']
                from_to = f"{row['from_job_name'][:22]} → {row['to_job_name'][:22]}"
                print(f"{from_to:<50} {row['skills_confidence']:.1f}%   "
                      f"{b['components']['overlap']:.1f}pts   "
                      f"{b['components']['coverage']:.1f}pts    "
                      f"{b['components']['rarity_bonus']:.1f}pts  "
                      f"{b['components']['gateway_bonus']:.1f}pts   "
                      f"{b['source_skills_count']}→{b['target_skills_count']} ({b['overlap_count']} overlap)")
        
        print(f"\n💡 COMPONENT INTERPRETATION:")
        print(f"   • Overlap (35% weight): How many source skills are found in target role")
        print(f"   • Coverage (35% weight): How well source skills cover target requirements")  
        print(f"   • Rarity (20% weight): Bonus for rare/exceptional skill overlaps")
        print(f"   • Gateway (10% weight): Bonus for cross-functional gateway skills")
        print(f"   • Skills format: source_count → target_count (overlap_count shared)")
        print("-" * 120)
        
        return {
            'results_df': skills_analysis_df,
            'gateway_skills_count': len(gateway_skills_set),
            'total_job_profiles': len(jobs_df),
            'total_skills': len(skills_df),
            'processing_summary': {
                'total_pairs_evaluated': total_pairs,
                'high_confidence_pairs': len(skills_analysis_df),
                'confidence_threshold': CONFIDENCE_THRESHOLD
            }
        }
        
    finally:
        conn.close()
        print("🔒 Database connection closed")

if __name__ == "__main__":
    results = main()
    print(f"\n{'='*80}")
    print("SKILLS INTELLIGENCE PREDICTIVE ANALYSIS COMPLETE")
    print(f"{'='*80}") 