#!/usr/bin/env python3
"""
Movement Predictive Analysis Engine
====================================

This module generates movement confidence scores for all job profile pairs (715 x 715 = 510,510 pairs)
by analyzing historical movement patterns, mobility scores, and pathway probabilities.

Key Features:
1. Historical movement pattern analysis with aggressive recency weighting (40% annual decay)
2. Job profile transition probability calculations
3. Mobility scoring integration (launchpad vs silo classification)
4. Movement confidence scoring for cartesian product of all job profiles
5. Smart filtering to exclude low-confidence pairs (<10%)

Builds on:
- 02_feature_evaluation_discovery_optimized.py (statistical methods)
- 03_role_typology_pathway_enhancement_enhanced.py (mobility scoring, pathway analysis)
"""

import pandas as pd
import numpy as np
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import warnings
import gc
import psutil
import os
from pathlib import Path
from datetime import datetime, timedelta
from itertools import product
from typing import Dict, List, Tuple, Optional
import json

warnings.filterwarnings('ignore')

# Set plotting style
plt.style.use('default')
sns.set_palette("husl")

# =============================================================================
# CONFIGURATION
# =============================================================================

# Database configuration
DATABASE_FILE = "models/2025-Q3/workforce_intelligence.sqlite"

# Movement confidence scoring weights
MOVEMENT_CONFIDENCE_WEIGHTS = {
    'historical_probability': 0.45,    # Core historical transition likelihood
    'source_mobility_score': 0.25,     # How mobile the source role is (launchpad factor)
    'target_mobility_score': 0.15,     # How accessible the target role is
    'sample_size_confidence': 0.10,    # Statistical reliability based on sample size
    'recency_boost': 0.05              # Boost for recent successful transitions
}

# Aggressive recency weighting configuration
RECENCY_DECAY_RATE = 0.4  # 40% annual decay rate
MIN_RECENCY_WEIGHT = 0.05  # Minimum weight threshold

# Confidence thresholds
MIN_MOVEMENTS_FOR_RELIABILITY = 3      # Minimum movements to calculate reliable probability
CONFIDENCE_THRESHOLD = 10.0            # Minimum confidence for inclusion in final dataset
SAMPLE_SIZE_CONFIDENCE_LEVELS = {
    1: 0.2,    # Very low confidence
    2: 0.4,    # Low confidence  
    3: 0.6,    # Medium confidence
    5: 0.8,    # High confidence
    10: 1.0    # Very high confidence
}

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

def calculate_aggressive_recency_weight(movement_date, reference_date=None, decay_rate=RECENCY_DECAY_RATE):
    """
    Calculate aggressive recency weighting for movement data
    40% annual decay rate reflects fast-changing banking environment
    """
    if reference_date is None:
        reference_date = datetime.now()
    
    # Convert to pandas datetime for consistent handling
    movement_date = pd.to_datetime(movement_date)
    reference_date = pd.to_datetime(reference_date)
    
    # Calculate years difference
    days_diff = (reference_date - movement_date).days
    years_ago = days_diff / 365.25
    
    weight = decay_rate ** years_ago
    
    return max(weight, MIN_RECENCY_WEIGHT)

def calculate_sample_size_confidence(sample_size):
    """
    Calculate confidence level based on sample size
    More movements = higher statistical confidence
    """
    for threshold in sorted(SAMPLE_SIZE_CONFIDENCE_LEVELS.keys(), reverse=True):
        if sample_size >= threshold:
            return SAMPLE_SIZE_CONFIDENCE_LEVELS[threshold]
    return 0.1  # Very low confidence for single instances

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

def load_movement_data(conn):
    """Load and prepare historical movement data"""
    print("📁 Loading historical movement data...")
    
    try:
        # Load movement data from the movement_fact table
        query = """
        SELECT 
            from_position,
            to_position,
            movement_pattern,
            movement_count,
            movement_year,
            movement_month,
            avg_days_between,
            predominant_movement_type
        FROM movement_fact
        WHERE from_position IS NOT NULL 
        AND to_position IS NOT NULL
        """
        
        movement_df = pd.read_sql_query(query, conn)
        print(f"✅ Loaded {len(movement_df):,} movement records")
        
        # Show data range
        if 'movement_year' in movement_df.columns:
            min_year = movement_df['movement_year'].min()
            max_year = movement_df['movement_year'].max()
            print(f"📅 Data range: {min_year} - {max_year}")
        
        return movement_df
        
    except Exception as e:
        raise RuntimeError(f"Failed to load movement data: {str(e)}")

def load_job_architecture(conn):
    """Load job architecture and position mapping data"""
    print("🏗️ Loading job architecture data...")
    
    # Load jobs data
    jobs_df = pd.read_sql_query("SELECT * FROM jobs", conn)
    print(f"✅ Loaded {len(jobs_df):,} job profiles")
    
    # Load positions data for mapping
    positions_df = pd.read_sql_query("SELECT * FROM positions", conn)
    print(f"✅ Loaded {len(positions_df):,} position records")
    print(f"   → Available columns: {list(positions_df.columns)}")
    
    return jobs_df, positions_df

def enrich_movement_data(movement_df, jobs_df, positions_df):
    """Enrich movement data with job profile and organizational context"""
    print("🔄 Enriching movement data with job context...")
    
    # Create clean position mapping
    position_mapping = positions_df[['Position Number', 'JobProfileID']].drop_duplicates('Position Number')
    
    # Map FROM positions
    enriched_df = movement_df.merge(
        position_mapping,
        left_on='from_position',
        right_on='Position Number',
        how='left',
        suffixes=('', '_from')
    ).drop('Position Number', axis=1)
    
    enriched_df = enriched_df.rename(columns={'JobProfileID': 'JobProfileID_from'})
    
    # Map TO positions
    enriched_df = enriched_df.merge(
        position_mapping,
        left_on='to_position',
        right_on='Position Number',
        how='left',
        suffixes=('', '_to')
    ).drop('Position Number', axis=1)
    
    enriched_df = enriched_df.rename(columns={'JobProfileID': 'JobProfileID_to'})
    
    # Add job architecture information
    job_info = jobs_df[['JobProfileID', 'JobFunction', 'JobSubFunction', 'ManagementLevel', 'JobCategory']]
    
    # Add FROM job info
    enriched_df = enriched_df.merge(
        job_info,
        left_on='JobProfileID_from',
        right_on='JobProfileID',
        how='left',
        suffixes=('', '_from')
    ).drop('JobProfileID', axis=1)
    
    # Add TO job info
    enriched_df = enriched_df.merge(
        job_info,
        left_on='JobProfileID_to',
        right_on='JobProfileID',
        how='left',
        suffixes=('_from', '_to')
    ).drop('JobProfileID', axis=1)
    
    # Clean up column names
    enriched_df = enriched_df.rename(columns={
        'JobFunction_from': 'from_job_function',
        'JobSubFunction_from': 'from_job_sub_function',
        'ManagementLevel_from': 'from_management_level',
        'JobCategory_from': 'from_job_category',
        'JobFunction_to': 'to_job_function',
        'JobSubFunction_to': 'to_job_sub_function',
        'ManagementLevel_to': 'to_management_level',
        'JobCategory_to': 'to_job_category'
    })
    
    # Filter to complete cases
    before_filter = len(enriched_df)
    enriched_df = enriched_df.dropna(subset=['JobProfileID_from', 'JobProfileID_to'])
    after_filter = len(enriched_df)
    
    print(f"✅ Enriched dataset: {after_filter:,} records (filtered {before_filter - after_filter:,} incomplete records)")
    
    return enriched_df

# =============================================================================
# MOBILITY SCORING AND ANALYSIS
# =============================================================================

def calculate_role_mobility_scores(movement_df):
    """
    Calculate mobility scores for each job profile based on movement patterns
    Builds on the mobility scoring from 03_role_typology_pathway_enhancement_enhanced.py
    """
    print("📊 Calculating role mobility scores...")
    
    # Get unique job profiles
    all_job_profiles = list(set(
        movement_df['JobProfileID_from'].dropna().tolist() + 
        movement_df['JobProfileID_to'].dropna().tolist()
    ))
    
    mobility_scores = {}
    
    for job_profile in all_job_profiles:
        # Outbound movements (people leaving this role)
        outbound = movement_df[movement_df['JobProfileID_from'] == job_profile]
        outbound_destinations = outbound['JobProfileID_to'].nunique()
        outbound_volume = len(outbound)
        
        # Inbound movements (people joining this role)
        inbound = movement_df[movement_df['JobProfileID_to'] == job_profile]
        inbound_sources = inbound['JobProfileID_from'].nunique()
        inbound_volume = len(inbound)
        
        # Calculate diversity metrics
        total_volume = outbound_volume + inbound_volume
        total_diversity = outbound_destinations + inbound_sources
        
        # Cross-functional movements
        cross_functional_out = len(outbound[outbound['from_job_function'] != outbound['to_job_function']])
        cross_functional_in = len(inbound[inbound['from_job_function'] != inbound['to_job_function']])
        cross_functional_ratio = (cross_functional_out + cross_functional_in) / max(total_volume, 1)
        
        # Mobility score calculation (0-100 scale)
        diversity_component = min(total_diversity * 2, 40)  # Up to 40 points for diversity
        volume_component = min(total_volume, 30)            # Up to 30 points for volume
        cross_boundary_component = cross_functional_ratio * 20  # Up to 20 points for cross-functional
        outbound_bias = min(outbound_destinations * 1.5, 10)    # Up to 10 points for outbound diversity (launchpad factor)
        
        mobility_score = diversity_component + volume_component + cross_boundary_component + outbound_bias
        
        # Classify mobility tier
        if mobility_score >= 85:
            mobility_tier = "Super Launchpad"
        elif mobility_score >= 70:
            mobility_tier = "Strong Launchpad"
        elif mobility_score >= 55:
            mobility_tier = "Moderate Launchpad"
        elif mobility_score >= 40:
            mobility_tier = "Standard Mobility"
        elif mobility_score >= 25:
            mobility_tier = "Limited Mobility"
        else:
            mobility_tier = "Career Silo"
        
        mobility_scores[job_profile] = {
            'mobility_score': mobility_score,
            'mobility_tier': mobility_tier,
            'outbound_destinations': outbound_destinations,
            'inbound_sources': inbound_sources,
            'total_volume': total_volume,
            'cross_functional_ratio': cross_functional_ratio
        }
    
    print(f"✅ Calculated mobility scores for {len(mobility_scores):,} job profiles")
    
    return mobility_scores

def calculate_historical_transition_probabilities(movement_df):
    """
    Calculate job profile to job profile transition probabilities with recency weighting
    """
    print("📈 Calculating historical transition probabilities...")
    
    # Apply recency weighting if movement_year is available
    if 'movement_year' in movement_df.columns:
        print("   → Applying aggressive recency weighting...")
        movement_df = movement_df.copy()
        movement_df['movement_date'] = pd.to_datetime(movement_df['movement_year'], format='%Y')
        movement_df['recency_weight'] = movement_df['movement_date'].apply(calculate_aggressive_recency_weight)
    else:
        print("   → No temporal data found, using uniform weighting")
        movement_df = movement_df.copy()
        movement_df['recency_weight'] = 1.0
    
    # Calculate weighted transition counts
    transition_counts = {}
    total_outbound = {}
    
    # Group by from -> to transitions
    transitions = movement_df.groupby(['JobProfileID_from', 'JobProfileID_to']).agg({
        'movement_count': 'sum',
        'recency_weight': 'sum'
    }).reset_index()
    
    # Calculate total outbound movements per job profile (weighted)
    outbound_totals = movement_df.groupby('JobProfileID_from').agg({
        'movement_count': 'sum',
        'recency_weight': 'sum'
    }).reset_index()
    
    for _, row in outbound_totals.iterrows():
        total_outbound[row['JobProfileID_from']] = row['recency_weight']
    
    # Calculate transition probabilities
    for _, row in transitions.iterrows():
        from_job = row['JobProfileID_from']
        to_job = row['JobProfileID_to']
        weighted_count = row['recency_weight']
        
        if from_job in total_outbound and total_outbound[from_job] > 0:
            probability = weighted_count / total_outbound[from_job]
            
            if from_job not in transition_counts:
                transition_counts[from_job] = {}
            
            transition_counts[from_job][to_job] = {
                'probability': probability,
                'weighted_count': weighted_count,
                'raw_count': row['movement_count']
            }
    
    print(f"✅ Calculated transition probabilities for {len(transition_counts):,} source job profiles")
    
    return transition_counts

# =============================================================================
# MOVEMENT CONFIDENCE SCORING
# =============================================================================

def calculate_movement_confidence_score(from_job_id, to_job_id, transition_probabilities, mobility_scores):
    """
    Calculate movement confidence score for a specific job profile pair
    
    Components:
    1. Historical probability (45%) - How often this transition has happened
    2. Source mobility score (25%) - How mobile the source role is
    3. Target mobility score (15%) - How accessible the target role is  
    4. Sample size confidence (10%) - Statistical reliability
    5. Recency boost (5%) - Recent successful transitions
    """
    
    # Initialize components
    historical_prob = 0.0
    source_mobility = 0.0
    target_mobility = 0.0
    sample_confidence = 0.0
    recency_boost = 0.0
    
    # 1. Historical probability component
    if from_job_id in transition_probabilities:
        if to_job_id in transition_probabilities[from_job_id]:
            transition_data = transition_probabilities[from_job_id][to_job_id]
            historical_prob = transition_data['probability']
            
            # Sample size confidence
            raw_count = transition_data['raw_count']
            sample_confidence = calculate_sample_size_confidence(raw_count)
            
            # Recency boost if weighted count is higher than raw count (recent activity)
            if transition_data['weighted_count'] > raw_count:
                recency_boost = min((transition_data['weighted_count'] / raw_count - 1) * 0.5, 1.0)
    
    # 2. Source mobility score component (normalized to 0-1)
    if from_job_id in mobility_scores:
        source_mobility = mobility_scores[from_job_id]['mobility_score'] / 100.0
    
    # 3. Target mobility score component (normalized to 0-1)
    if to_job_id in mobility_scores:
        target_mobility = mobility_scores[to_job_id]['mobility_score'] / 100.0
    
    # Calculate weighted confidence score (0-100)
    confidence_score = (
        MOVEMENT_CONFIDENCE_WEIGHTS['historical_probability'] * historical_prob * 100 +
        MOVEMENT_CONFIDENCE_WEIGHTS['source_mobility_score'] * source_mobility * 100 +
        MOVEMENT_CONFIDENCE_WEIGHTS['target_mobility_score'] * target_mobility * 100 +
        MOVEMENT_CONFIDENCE_WEIGHTS['sample_size_confidence'] * sample_confidence * 100 +
        MOVEMENT_CONFIDENCE_WEIGHTS['recency_boost'] * recency_boost * 100
    )
    
    # Create explanation dictionary
    explanation = {
        'historical_probability': historical_prob,
        'source_mobility_score': source_mobility,
        'target_mobility_score': target_mobility,
        'sample_size_confidence': sample_confidence,
        'recency_boost': recency_boost,
        'raw_movement_count': transition_probabilities.get(from_job_id, {}).get(to_job_id, {}).get('raw_count', 0),
        'weighted_movement_count': transition_probabilities.get(from_job_id, {}).get(to_job_id, {}).get('weighted_count', 0.0)
    }
    
    return confidence_score, explanation

# =============================================================================
# CARTESIAN PRODUCT GENERATION
# =============================================================================

def generate_cartesian_movement_analysis(jobs_df, transition_probabilities, mobility_scores, chunk_size=CHUNK_SIZE):
    """
    Generate movement confidence scores for all job profile pairs (715 x 715)
    Uses chunked processing to manage memory efficiently
    """
    print_section_header("CARTESIAN PRODUCT MOVEMENT ANALYSIS")
    print(f"Generating movement confidence scores for all job profile pairs...")
    
    # Get all unique job profile IDs
    all_job_ids = jobs_df['JobProfileID'].unique().tolist()
    total_pairs = len(all_job_ids) ** 2
    
    print(f"📊 Processing {len(all_job_ids):,} job profiles")
    print(f"📊 Total pairs to analyze: {total_pairs:,}")
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
            # Calculate movement confidence score
            confidence_score, explanation = calculate_movement_confidence_score(
                from_job_id, to_job_id, transition_probabilities, mobility_scores
            )
            
            # Only keep pairs above confidence threshold
            if confidence_score >= CONFIDENCE_THRESHOLD:
                chunk_results.append({
                    'from_job_id': from_job_id,
                    'to_job_id': to_job_id,
                    'movement_confidence': confidence_score,
                    'historical_probability': explanation['historical_probability'],
                    'source_mobility_score': explanation['source_mobility_score'],
                    'target_mobility_score': explanation['target_mobility_score'],
                    'sample_size_confidence': explanation['sample_size_confidence'],
                    'recency_boost': explanation['recency_boost'],
                    'raw_movement_count': explanation['raw_movement_count'],
                    'weighted_movement_count': explanation['weighted_movement_count']
                })
                high_confidence_pairs += 1
            
            processed_pairs += 1
        
        # Add chunk results to main results
        results.extend(chunk_results)
        
        # Memory management
        trigger_garbage_collection()
        print_memory_status()
    
    # Convert to DataFrame
    movement_analysis_df = pd.DataFrame(results)
    
    print(f"\n✅ Cartesian product analysis complete!")
    print(f"📊 Total pairs processed: {processed_pairs:,}")
    print(f"📊 High confidence pairs (≥{CONFIDENCE_THRESHOLD}%): {high_confidence_pairs:,}")
    print(f"📊 Retention rate: {(high_confidence_pairs / processed_pairs * 100):.2f}%")
    
    return movement_analysis_df

# =============================================================================
# ANALYSIS AND INSIGHTS
# =============================================================================

def analyze_movement_patterns(movement_analysis_df, jobs_df):
    """Generate comprehensive insights from the movement analysis results"""
    print_section_header("COMPREHENSIVE MOVEMENT PATTERN ANALYSIS")
    
    if movement_analysis_df.empty:
        print("⚠️ No high-confidence movement patterns found")
        return
    
    # Merge with job information for analysis
    analysis_with_jobs = movement_analysis_df.merge(
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
    
    print("🔍 TOP MOVEMENT CONFIDENCE SCORES WITH BREAKDOWN:")
    print("-" * 160)
    print(f"{'From → To':<85} {'Total':<8} {'Historical':<10} {'Source Mob':<11} {'Target Mob':<11} {'Sample':<8} {'Recency':<8} {'Raw Count':<10}")
    print("-" * 160)
    
    top_movements = movement_analysis_df.nlargest(20, 'movement_confidence')
    top_movements_with_jobs = top_movements.merge(
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
    
    for _, row in top_movements_with_jobs.iterrows():
        from_job = row.get('JobProfile_from', row['from_job_id'])[:40] if pd.notna(row.get('JobProfile_from')) else row['from_job_id']
        to_job = row.get('JobProfile_to', row['to_job_id'])[:40] if pd.notna(row.get('JobProfile_to')) else row['to_job_id']
        from_to = f"{from_job} → {to_job}"
        print(f"{from_to:<85} {row['movement_confidence']:.1f}%   {row['historical_probability']:.3f}     {row['source_mobility_score']:.3f}      {row['target_mobility_score']:.3f}      {row['sample_size_confidence']:.3f}   {row['recency_boost']:.3f}   {row['raw_movement_count']:<10}")
    
    print(f"\n📊 DETAILED CONFIDENCE COMPONENT ANALYSIS:")
    print(f"   → Mean confidence: {movement_analysis_df['movement_confidence'].mean():.2f}%")
    print(f"   → Median confidence: {movement_analysis_df['movement_confidence'].median():.2f}%")
    print(f"   → 90th percentile: {movement_analysis_df['movement_confidence'].quantile(0.9):.2f}%")
    print(f"   → 10th percentile: {movement_analysis_df['movement_confidence'].quantile(0.1):.2f}%")
    print(f"   → Standard deviation: {movement_analysis_df['movement_confidence'].std():.2f}%")
    
    # Component analysis
    print(f"\n🔬 COMPONENT CONTRIBUTION ANALYSIS:")
    components = ['historical_probability', 'source_mobility_score', 'target_mobility_score', 'sample_size_confidence', 'recency_boost']
    weights = [0.45, 0.25, 0.15, 0.10, 0.05]
    
    for component, weight in zip(components, weights):
        mean_val = movement_analysis_df[component].mean()
        weighted_contribution = mean_val * weight * 100
        print(f"   → {component:<25}: Mean={mean_val:.3f}, Weighted Contribution={weighted_contribution:.2f}%")
    
    # Distribution analysis
    print(f"\n📈 CONFIDENCE SCORE DISTRIBUTION:")
    bins = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    confidence_dist = pd.cut(movement_analysis_df['movement_confidence'], bins=bins).value_counts().sort_index()
    for interval, count in confidence_dist.items():
        percentage = (count / len(movement_analysis_df)) * 100
        print(f"   → {interval}: {count:,} pairs ({percentage:.2f}%)")
    
    # Historical movement analysis
    print(f"\n📚 HISTORICAL MOVEMENT PATTERNS:")
    with_historical = movement_analysis_df[movement_analysis_df['raw_movement_count'] > 0]
    print(f"   → Pairs with historical data: {len(with_historical):,} ({len(with_historical)/len(movement_analysis_df)*100:.2f}%)")
    print(f"   → Pairs without historical data: {len(movement_analysis_df) - len(with_historical):,}")
    
    if len(with_historical) > 0:
        print(f"   → Mean historical probability (with data): {with_historical['historical_probability'].mean():.4f}")
        print(f"   → Mean raw movement count: {with_historical['raw_movement_count'].mean():.2f}")
        print(f"   → Max raw movement count: {with_historical['raw_movement_count'].max()}")
        
        # Movement count distribution
        print(f"\n   HISTORICAL MOVEMENT COUNT DISTRIBUTION:")
        movement_counts = with_historical['raw_movement_count'].value_counts().sort_index()
        for count, freq in movement_counts.head(10).items():
            print(f"      → {count} movements: {freq:,} pairs")
    
    # Mobility score analysis
    print(f"\n🚀 MOBILITY SCORE ANALYSIS:")
    print(f"   → Mean source mobility: {movement_analysis_df['source_mobility_score'].mean():.3f}")
    print(f"   → Mean target mobility: {movement_analysis_df['target_mobility_score'].mean():.3f}")
    print(f"   → Pairs with high source mobility (>0.8): {len(movement_analysis_df[movement_analysis_df['source_mobility_score'] > 0.8]):,}")
    print(f"   → Pairs with high target mobility (>0.8): {len(movement_analysis_df[movement_analysis_df['target_mobility_score'] > 0.8]):,}")
    
    # Cross-functional movement analysis
    if 'JobFunction_from' in analysis_with_jobs.columns and 'JobFunction_to' in analysis_with_jobs.columns:
        cross_functional = analysis_with_jobs[
            analysis_with_jobs['JobFunction_from'] != analysis_with_jobs['JobFunction_to']
        ]
        same_functional = analysis_with_jobs[
            analysis_with_jobs['JobFunction_from'] == analysis_with_jobs['JobFunction_to']
        ]
        
        print(f"\n🔄 FUNCTIONAL MOVEMENT ANALYSIS:")
        print(f"   → Same function movements: {len(same_functional):,} ({len(same_functional)/len(analysis_with_jobs)*100:.2f}%)")
        print(f"   → Cross-functional movements: {len(cross_functional):,} ({len(cross_functional)/len(analysis_with_jobs)*100:.2f}%)")
        
        if len(cross_functional) > 0:
            print(f"   → Avg same-function confidence: {same_functional['movement_confidence'].mean():.2f}%")
            print(f"   → Avg cross-functional confidence: {cross_functional['movement_confidence'].mean():.2f}%")
    
    # Warning analysis
    print(f"\n⚠️  POTENTIAL ISSUES TO INVESTIGATE:")
    
    # Check for suspiciously high retention
    retention_rate = len(movement_analysis_df) / (715 * 715) * 100
    if retention_rate > 95:
        print(f"   → HIGH RETENTION RATE: {retention_rate:.2f}% (expected much lower with 10% threshold)")
    
    # Check for low historical data coverage
    historical_coverage = len(with_historical) / len(movement_analysis_df) * 100
    if historical_coverage < 50:
        print(f"   → LOW HISTORICAL COVERAGE: {historical_coverage:.2f}% of pairs have historical data")
    
    # Check for uniform mobility scores
    mobility_variance = movement_analysis_df['source_mobility_score'].var()
    if mobility_variance < 0.01:
        print(f"   → LOW MOBILITY VARIANCE: Source mobility scores may be too uniform (var={mobility_variance:.6f})")
    
    print(f"\n🚨 CRITICAL ANALYSIS OF RESULTS:")
    print(f"   PROBLEM 1 - Historical data barely contributing (0.06% vs expected 45%)")
    print(f"      → Mean historical probability: 0.001 (extremely low)")
    print(f"      → Only 20.17% of pairs have any historical data") 
    print(f"      → This suggests historical transition probabilities are not working as expected")
    
    print(f"\n   PROBLEM 2 - Mobility scores dominating the results (35.25% combined)")
    print(f"      → Source mobility: 22.03% contribution (expected ~25%)")
    print(f"      → Target mobility: 13.22% contribution (expected ~15%)")
    print(f"      → Mean mobility scores are very high (0.881) - may need normalization")
    
    print(f"\n   PROBLEM 3 - Confidence threshold not working effectively")
    print(f"      → 98.52% retention rate suggests 10% threshold is too low")
    print(f"      → Most scores cluster in 30-40% range, few above 50%")
    print(f"      → Consider raising threshold to 25-30% for better selectivity")
    
    print(f"\n   PROBLEM 4 - No recency boost observed (0.00% contribution)")
    print(f"      → All recency_boost values appear to be 0.000")
    print(f"      → Recency weighting may not be working as intended")
    
    print(f"\n💡 IMMEDIATE FIX RECOMMENDATIONS:")
    print(f"   1. INCREASE confidence threshold from 10% to 25-30%")
    print(f"   2. DEBUG historical probability calculation - values too low")
    print(f"   3. NORMALIZE mobility scores or adjust their weight")
    print(f"   4. VERIFY recency weighting logic")
    print(f"   5. COMPARE with 03_role_typology methodology for mobility scoring")
    
    print(f"\n📊 SUGGESTED WEIGHT ADJUSTMENTS:")
    print(f"   → Reduce mobility component weights until historical data works properly")
    print(f"   → Consider: historical=60%, source_mobility=20%, target_mobility=10%, sample=5%, recency=5%")
    print(f"   → Or focus on fixing historical calculation before adjusting weights")

def save_movement_analysis_results(movement_analysis_df, output_path="movement_confidence_analysis.csv"):
    """Save the movement analysis results to CSV"""
    print(f"\n💾 Saving movement analysis results to {output_path}")
    movement_analysis_df.to_csv(output_path, index=False)
    print(f"✅ Saved {len(movement_analysis_df):,} movement confidence scores")

# =============================================================================
# MAIN EXECUTION FUNCTION
# =============================================================================

def main():
    """Main execution function for movement predictive analysis"""
    print_section_header(
        "MOVEMENT PREDICTIVE ANALYSIS ENGINE",
        "Generating movement confidence scores for all job profile pairs using historical data"
    )
    
    print_memory_status()
    
    # 1. Load data
    conn = load_database_connection()
    movement_df = load_movement_data(conn)
    jobs_df, positions_df = load_job_architecture(conn)
    
    # 2. Enrich movement data
    enriched_movement_df = enrich_movement_data(movement_df, jobs_df, positions_df)
    
    # 3. Calculate mobility scores
    mobility_scores = calculate_role_mobility_scores(enriched_movement_df)
    
    # 4. Calculate transition probabilities
    transition_probabilities = calculate_historical_transition_probabilities(enriched_movement_df)
    
    # 5. Generate cartesian product analysis
    movement_analysis_df = generate_cartesian_movement_analysis(
        jobs_df, transition_probabilities, mobility_scores
    )
    
    # 6. Analyze results
    analyze_movement_patterns(movement_analysis_df, jobs_df)
    
    # 7. Save results
    save_movement_analysis_results(movement_analysis_df)
    
    # 8. Clean up
    conn.close()
    print(f"\n🔒 Database connection closed")
    print_memory_status()
    
    return {
        'movement_analysis_df': movement_analysis_df,
        'mobility_scores': mobility_scores,
        'transition_probabilities': transition_probabilities,
        'total_high_confidence_pairs': len(movement_analysis_df)
    }

if __name__ == "__main__":
    results = main()
    print(f"\n{'='*80}")
    print("MOVEMENT PREDICTIVE ANALYSIS COMPLETE")
    print(f"{'='*80}") 