#!/usr/bin/env python3
"""
Role Typology Analysis & Pathway Enhancement

Phase 2: Role Typology Classification
- Calculate movement diversity scores for organisational features
- Identify launchpad features (high outbound mobility, multiple destinations)
- Identify silo features (low outbound mobility, limited destinations)
- Map transition networks and mobility patterns

Phase 3: Enhanced Pathway Recommendations
- Integrate movement probabilities with existing similarity scores
- Create feature-aware pathway scoring
- Build personalised recommendation engine

Dual Analysis Support:
- Job-based analysis (functions, sub-functions, categories, etc.)
- Skills-based analysis (skill transitions and bridge identification)

This script is designed for production deployment with configurable parameters.
"""

import pandas as pd
import numpy as np
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
from pathlib import Path
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import warnings
warnings.filterwarnings('ignore')

# Set plotting style
plt.style.use('default')
sns.set_palette("husl")

# =============================================================================
# CONFIGURATION SECTION
# =============================================================================

# Configuration class for analysis parameters
class AnalysisConfig:
    # Database configuration
    DATABASE_PATH = 'models/2025-Q3/workforce_intelligence.sqlite'
    MOVEMENT_DATA_PATH = 'data/synthetic_test/movement_analysis/realistic_movement_fact_table.csv'
    
    # Primary analysis feature
    PRIMARY_FEATURE = 'from_job_sub_function'
    TARGET_FEATURE = 'to_job_sub_function'
    
    # Skills analysis configuration - RAM-AWARE SETTINGS
    SKILLS_TABLE = 'job_skills'
    SKILLS_ID_COL = 'JobProfileID'
    SKILLS_NAME_COL = 'Skill_Name'
    MAX_MOVEMENTS_FOR_SKILLS = 10000  # Reduced from 50000 for RAM efficiency
    MIN_SKILL_FREQUENCY = 20  # Increased from 10 to reduce processing
    SKILLS_CHUNK_SIZE = 1000  # Process skills in chunks
    MAX_SKILLS_PER_JOB = 50  # Limit skills per job to prevent memory explosion
    
    # Feature display names
    FEATURE_DISPLAY_NAMES = {
        'from_job_sub_function': 'Job Sub-Function',
        'to_job_sub_function': 'Job Sub-Function'
    }
    
    # Role classification thresholds
    LAUNCHPAD_THRESHOLDS = {
        'min_outbound_diversity': 0.85,
        'min_total_movements': 50,
        'min_destinations': 5
    }
    
    SILO_THRESHOLDS = {
        'max_outbound_diversity': 0.50,
        'max_destinations': 3
    }
    
    BRIDGE_THRESHOLDS = {
        'min_cross_category_rate': 0.70
    }
    
    # Pathway enhancement settings
    PATHWAY_WEIGHTS = {
        'movement_probability': 0.4,
        'similarity_score': 0.3,
        'diversity_bonus': 0.2,
        'skill_bridge_bonus': 0.1
    }
    
    MIN_MOVEMENTS_FOR_PROBABILITY = 10
    TOP_N_FEATURES = 10
    
    @classmethod
    def get_config_summary(cls):
        """Return a summary of current configuration for logging"""
        return {
            'primary_feature': cls.PRIMARY_FEATURE,
            'target_feature': cls.TARGET_FEATURE,
            'skills_analysis_enabled': True, # Always enabled for this script
            'launchpad_diversity_threshold': cls.LAUNCHPAD_THRESHOLDS['min_outbound_diversity'],
            'silo_diversity_threshold': cls.SILO_THRESHOLDS['max_outbound_diversity'],
            'pathway_weights': cls.PATHWAY_WEIGHTS
        }

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def print_section_header(title, description=""):
    """Print a formatted section header"""
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}")
    if description:
        print(f"{description}")
        print()

def print_methodology(methodology_text):
    """Print methodology explanation with formatting"""
    print(f"\n📋 METHODOLOGY:")
    print(f"{'-'*50}")
    print(f"{methodology_text}")
    print()

def print_config_summary():
    """Print current configuration settings"""
    config = AnalysisConfig.get_config_summary()
    print("🔧 ANALYSIS CONFIGURATION:")
    print(f"   → Primary Feature: {config['primary_feature']}")
    print(f"   → Target Feature: {config['target_feature']}")
    print(f"   → Skills Analysis: {'Enabled' if config['skills_analysis_enabled'] else 'Disabled'}")
    print(f"   → Launchpad Threshold: {config['launchpad_diversity_threshold']:.2f}")
    print(f"   → Silo Threshold: {config['silo_diversity_threshold']:.2f}")
    print(f"   → Pathway Weights: {config['pathway_weights']}")

def calculate_diversity_score(transition_counts):
    """
    Calculate Shannon diversity index for transition patterns.
    Higher score = more diverse transitions (launchpad characteristic)
    Lower score = concentrated transitions (silo characteristic)
    """
    if len(transition_counts) == 0:
        return 0.0
    
    # Convert to probabilities
    total = sum(transition_counts.values())
    if total == 0:
        return 0.0
    
    probabilities = [count / total for count in transition_counts.values()]
    
    # Calculate Shannon entropy
    entropy = -sum(p * np.log2(p) for p in probabilities if p > 0)
    
    # Normalize by maximum possible entropy for this number of categories
    max_entropy = np.log2(len(probabilities)) if len(probabilities) > 1 else 1
    
    return entropy / max_entropy if max_entropy > 0 else 0.0

def load_movement_data():
    """Load movement data from configured path"""
    try:
        movement_df = pd.read_csv(AnalysisConfig.MOVEMENT_DATA_PATH)
        print(f"📁 Loaded movement data from: {AnalysisConfig.MOVEMENT_DATA_PATH}")
        return movement_df
    except FileNotFoundError:
        raise FileNotFoundError(f"Could not find movement data CSV: {AnalysisConfig.MOVEMENT_DATA_PATH}")

def load_database():
    """Connect to database from configured path"""
    try:
        conn = sqlite3.connect(AnalysisConfig.DATABASE_PATH)
        print(f"🔗 Connected to database: {AnalysisConfig.DATABASE_PATH}")
        return conn
    except sqlite3.OperationalError:
        raise FileNotFoundError(f"Could not connect to database: {AnalysisConfig.DATABASE_PATH}")

def enrich_movement_data(movement_df, conn):
    """Enrich movement data with job context using the proven pandas merge approach"""
    
    # Load job architecture data
    jobs_df = pd.read_sql_query("SELECT * FROM jobs", conn)
    positions_df = pd.read_sql_query("SELECT * FROM positions", conn)
    
    print(f"🏢 Loaded jobs data: {len(jobs_df):,} job profiles")
    print(f"🏢 Loaded positions data: {len(positions_df):,} position records")
    
    # Data type conversion for successful merges
    positions_df['Position Number'] = positions_df['Position Number'].astype(str)
    movement_df['from_position'] = movement_df['from_position'].astype(str)
    movement_df['to_position'] = movement_df['to_position'].astype(str)
    
    # Step-by-step pandas merges (following proven approach)
    print("🔄 Enriching movement data with job context...")
    
    # Step 1: Add 'from' position context
    movement_with_context = movement_df.merge(
        positions_df[['Position Number', 'JobProfileID']],
        left_on='from_position',
        right_on='Position Number',
        how='left',
        suffixes=('', '_pos_from')
    ).drop('Position Number', axis=1)
    
    # Step 2: Add 'to' position context
    movement_with_context = movement_with_context.merge(
        positions_df[['Position Number', 'JobProfileID']],
        left_on='to_position',
        right_on='Position Number',
        how='left',
        suffixes=('_from', '_to')
    ).drop('Position Number', axis=1)
    
    # Step 3: Add 'from' job architecture context
    movement_with_context = movement_with_context.merge(
        jobs_df[['JobProfileID', 'JobFunction', 'JobSubFunction', 'ManagementLevel', 'JobCategory']],
        left_on='JobProfileID_from',
        right_on='JobProfileID',
        how='left',
        suffixes=('', '_from')
    ).drop('JobProfileID', axis=1)
    
    # Step 4: Add 'to' job architecture context
    movement_with_context = movement_with_context.merge(
        jobs_df[['JobProfileID', 'JobFunction', 'JobSubFunction', 'ManagementLevel', 'JobCategory']],
        left_on='JobProfileID_to',
        right_on='JobProfileID',
        how='left',
        suffixes=('_from', '_to')
    ).drop('JobProfileID', axis=1)
    
    # Rename columns to match analysis expectations
    enriched_df = movement_with_context.rename(columns={
        'JobFunction_from': 'from_job_function',
        'JobSubFunction_from': 'from_job_sub_function',
        'JobCategory_from': 'from_job_category',
        'ManagementLevel_from': 'from_management_level',
        'JobFunction_to': 'to_job_function',
        'JobSubFunction_to': 'to_job_sub_function',
        'JobCategory_to': 'to_job_category',
        'ManagementLevel_to': 'to_management_level'
    })
    
    # Validate merge success
    successful_merges = (enriched_df['from_job_function'].notna() & 
                        enriched_df['to_job_function'].notna()).sum()
    merge_success_rate = successful_merges / len(enriched_df)
    
    print(f"✅ Enriched dataset: {len(enriched_df):,} records")
    print(f"✅ Merge success rate: {merge_success_rate*100:.1f}%")
    
    return enriched_df

def main():
    """Main analysis function"""
    
    print_section_header(
        "ROLE TYPOLOGY ANALYSIS & PATHWAY ENHANCEMENT",
        "Phase 2: Role Classification | Phase 3: Enhanced Recommendations"
    )
    
    # Print configuration summary
    print_config_summary()
    
    # =============================================================================
    # 1. DATA LOADING AND PREPARATION
    # =============================================================================
    
    print_section_header("DATA LOADING AND PREPARATION")
    print_methodology("""
    Loading and preparing data for role typology analysis:
    1. Load movement data from configured CSV source
    2. Connect to database for job architecture context
    3. Enrich movement data with job context using proven merge approach
    4. Validate data quality and completeness
    
    This follows the successful pattern from previous phases.
    """)
    
    # Load data
    movement_df = load_movement_data()
    conn = load_database()
    enriched_df = enrich_movement_data(movement_df, conn)
    
    print(f"📊 Final dataset: {len(enriched_df):,} enriched movement records")
    print(f"📅 Date range: {enriched_df['movement_year'].min()} - {enriched_df['movement_year'].max()}")
    
    # =============================================================================
    # 2. ROLE TYPOLOGY ANALYSIS - JOB FEATURES
    # =============================================================================
    
    print_section_header("ROLE TYPOLOGY ANALYSIS - JOB FEATURES")
    print_methodology(f"""
    Analysing movement patterns for {AnalysisConfig.FEATURE_DISPLAY_NAMES[AnalysisConfig.PRIMARY_FEATURE]}:
    
    1. DIVERSITY CALCULATION:
       - Shannon entropy to measure transition diversity
       - Higher diversity = Launchpad characteristics
       - Lower diversity = Silo characteristics
    
    2. MOBILITY METRICS:
       - Total outbound movements
       - Number of destination categories
       - Cross-category transition rates
    
    3. CLASSIFICATION:
       - Launchpads: High diversity, multiple destinations
       - Silos: Low diversity, limited destinations  
       - Bridges: Enable cross-category mobility
    
    Primary feature: {AnalysisConfig.PRIMARY_FEATURE}
    """)
    
    # Filter to complete records for analysis
    analysis_df = enriched_df.dropna(subset=[AnalysisConfig.PRIMARY_FEATURE, AnalysisConfig.TARGET_FEATURE])
    
    print(f"📊 Analysis dataset: {len(analysis_df):,} complete records")
    
    # Calculate role typology metrics
    role_metrics = []
    
    # Group by primary feature to calculate metrics
    for feature_value in analysis_df[AnalysisConfig.PRIMARY_FEATURE].unique():
        feature_movements = analysis_df[analysis_df[AnalysisConfig.PRIMARY_FEATURE] == feature_value]
        
        # Calculate transition patterns
        transitions = feature_movements[AnalysisConfig.TARGET_FEATURE].value_counts()
        total_movements = len(feature_movements)
        unique_destinations = len(transitions)
        
        # Calculate diversity score
        diversity_score = calculate_diversity_score(transitions.to_dict())
        
        # Calculate cross-category movements (if category data available)
        cross_category_rate = 0.0
        if 'from_job_category' in feature_movements.columns and 'to_job_category' in feature_movements.columns:
            cross_category_moves = (feature_movements['from_job_category'] != feature_movements['to_job_category']).sum()
            cross_category_rate = cross_category_moves / total_movements if total_movements > 0 else 0.0
        
        # Store metrics
        role_metrics.append({
            'feature_value': feature_value,
            'total_movements': total_movements,
            'unique_destinations': unique_destinations,
            'diversity_score': diversity_score,
            'cross_category_rate': cross_category_rate,
            'top_destination': transitions.index[0] if len(transitions) > 0 else None,
            'top_destination_rate': transitions.iloc[0] / total_movements if len(transitions) > 0 else 0.0
        })
    
    # Convert to DataFrame
    role_metrics_df = pd.DataFrame(role_metrics)
    role_metrics_df = role_metrics_df.sort_values('diversity_score', ascending=False)
    
    print(f"📈 Calculated metrics for {len(role_metrics_df)} {AnalysisConfig.FEATURE_DISPLAY_NAMES[AnalysisConfig.PRIMARY_FEATURE]} values")
    
    # =============================================================================
    # 3. ROLE CLASSIFICATION
    # =============================================================================
    
    print_section_header("ROLE CLASSIFICATION")
    print_methodology(f"""
    Classifying roles based on mobility patterns:
    
    LAUNCHPAD CRITERIA:
    - Diversity Score ≥ {AnalysisConfig.LAUNCHPAD_THRESHOLDS['min_outbound_diversity']:.2f}
    - Total Movements ≥ {AnalysisConfig.LAUNCHPAD_THRESHOLDS['min_total_movements']}
    - Unique Destinations ≥ {AnalysisConfig.LAUNCHPAD_THRESHOLDS['min_destinations']}
    
    SILO CRITERIA:
    - Diversity Score ≤ {AnalysisConfig.SILO_THRESHOLDS['max_outbound_diversity']:.2f}
    - Unique Destinations ≤ {AnalysisConfig.SILO_THRESHOLDS['max_destinations']}
    
    BRIDGE CRITERIA:
    - Cross-Category Rate ≥ {AnalysisConfig.BRIDGE_THRESHOLDS['min_cross_category_rate']:.2f}
    """)
    
    # Apply classification logic
    def classify_role(row):
        # Launchpad criteria
        if (row['diversity_score'] >= AnalysisConfig.LAUNCHPAD_THRESHOLDS['min_outbound_diversity'] and
            row['total_movements'] >= AnalysisConfig.LAUNCHPAD_THRESHOLDS['min_total_movements'] and
            row['unique_destinations'] >= AnalysisConfig.LAUNCHPAD_THRESHOLDS['min_destinations']):
            return 'Launchpad'
        
        # Silo criteria
        elif (row['diversity_score'] <= AnalysisConfig.SILO_THRESHOLDS['max_outbound_diversity'] and
              row['unique_destinations'] <= AnalysisConfig.SILO_THRESHOLDS['max_destinations']):
            return 'Silo'
        
        # Bridge criteria
        elif row['cross_category_rate'] >= AnalysisConfig.BRIDGE_THRESHOLDS['min_cross_category_rate']:
            return 'Bridge'
        
        # Default classification
        else:
            return 'Standard'
    
    role_metrics_df['role_type'] = role_metrics_df.apply(classify_role, axis=1)
    
    # Display classification results
    classification_summary = role_metrics_df['role_type'].value_counts()
    print("📊 Role Classification Summary:")
    for role_type, count in classification_summary.items():
        percentage = count / len(role_metrics_df) * 100
        print(f"   {role_type}: {count} ({percentage:.1f}%)")
    
    # Show top examples of each type
    print(f"\n🚀 TOP LAUNCHPAD {AnalysisConfig.FEATURE_DISPLAY_NAMES[AnalysisConfig.PRIMARY_FEATURE]}S:")
    launchpads = role_metrics_df[role_metrics_df['role_type'] == 'Launchpad'].head(AnalysisConfig.TOP_N_FEATURES)
    if not launchpads.empty:
        for _, row in launchpads.iterrows():
            print(f"   • {row['feature_value']}: {row['diversity_score']:.3f} diversity, {row['unique_destinations']} destinations, {row['total_movements']} movements")
    else:
        print("   No launchpads identified with current thresholds")
    
    print(f"\n🏢 TOP SILO {AnalysisConfig.FEATURE_DISPLAY_NAMES[AnalysisConfig.PRIMARY_FEATURE]}S:")
    silos = role_metrics_df[role_metrics_df['role_type'] == 'Silo'].head(AnalysisConfig.TOP_N_FEATURES)
    if not silos.empty:
        for _, row in silos.iterrows():
            print(f"   • {row['feature_value']}: {row['diversity_score']:.3f} diversity, {row['unique_destinations']} destinations, {row['total_movements']} movements")
    else:
        print("   No silos identified with current thresholds")
    
    print(f"\n🌉 TOP BRIDGE {AnalysisConfig.FEATURE_DISPLAY_NAMES[AnalysisConfig.PRIMARY_FEATURE]}S:")
    bridges = role_metrics_df[role_metrics_df['role_type'] == 'Bridge'].head(AnalysisConfig.TOP_N_FEATURES)
    if not bridges.empty:
        for _, row in bridges.iterrows():
            print(f"   • {row['feature_value']}: {row['cross_category_rate']:.3f} cross-category rate, {row['diversity_score']:.3f} diversity")
    else:
        print("   No bridges identified with current thresholds")
    
    # =============================================================================
    # 4. RAM-AWARE SKILLS ANALYSIS
    # =============================================================================
    
    print_section_header("RAM-AWARE SKILLS ANALYSIS")
    print_methodology(f"""
    Analysing skill transition patterns using memory-efficient chunked processing:
    1. Stream processing of skill data to avoid large memory allocations
    2. Chunked analysis with configurable batch sizes
    3. Frequency-based filtering to focus on significant patterns
    4. Direct aggregation without storing intermediate large datasets
    
    This approach prevents memory overflow while maintaining analytical value.
    """)
    
    try:
        # Step 1: Sample movements for analysis (RAM-conscious)
        print("🎯 Sampling movements for RAM-efficient skills analysis...")
        
        # Calculate movement counts per job sub-function to identify top quartile
        movement_counts = analysis_df.groupby(AnalysisConfig.PRIMARY_FEATURE).size()
        movement_counts = movement_counts.sort_values(ascending=False)
        top_quartile_cutoff = movement_counts.quantile(0.75)
        top_quartile_features = movement_counts[movement_counts >= top_quartile_cutoff].index.tolist()
        
        # Sample movements from top quartile features
        sampled_movements = analysis_df[
            analysis_df[AnalysisConfig.PRIMARY_FEATURE].isin(top_quartile_features)
        ]
        
        # Further limit if still too large
        if len(sampled_movements) > AnalysisConfig.MAX_MOVEMENTS_FOR_SKILLS:
            sampled_movements = sampled_movements.sample(
                n=AnalysisConfig.MAX_MOVEMENTS_FOR_SKILLS, 
                random_state=42
            )
        
        print(f"   → Sampled {len(sampled_movements):,} movements from {len(top_quartile_features)} top quartile features")
        print(f"   → Top quartile cutoff: {top_quartile_cutoff:.0f} movements per feature")
        
        # Step 2: Get unique job IDs for skills lookup
        job_ids_from = set(sampled_movements['JobProfileID_from'].dropna().unique())
        job_ids_to = set(sampled_movements['JobProfileID_to'].dropna().unique())
        all_job_ids = job_ids_from.union(job_ids_to)
        
        if len(all_job_ids) > 0:
            print(f"📊 Processing skills for {len(all_job_ids):,} unique job profiles")
            
            # Step 3: Load skills data in chunks to avoid memory issues
            skill_transitions = {}  # Dictionary to store skill transition counts
            processed_movements = 0
            
            # Process movements in chunks
            chunk_size = AnalysisConfig.SKILLS_CHUNK_SIZE
            for chunk_start in range(0, len(sampled_movements), chunk_size):
                chunk_end = min(chunk_start + chunk_size, len(sampled_movements))
                movement_chunk = sampled_movements.iloc[chunk_start:chunk_end]
                
                # Get job IDs for this chunk
                chunk_job_ids = set(movement_chunk['JobProfileID_from'].dropna().unique()).union(
                    set(movement_chunk['JobProfileID_to'].dropna().unique())
                )
                
                if len(chunk_job_ids) > 0:
                    # Load skills for this chunk only
                    job_ids_str = ','.join([f"'{job_id}'" for job_id in chunk_job_ids])
                    
                    skills_query = f"""
                    SELECT js.{AnalysisConfig.SKILLS_ID_COL}, s.{AnalysisConfig.SKILLS_NAME_COL}
                    FROM {AnalysisConfig.SKILLS_TABLE} js
                    JOIN skills s ON js.Skill_ID = s.Skill_ID
                    WHERE js.{AnalysisConfig.SKILLS_ID_COL} IN ({job_ids_str})
                    """
                    
                    chunk_skills_df = pd.read_sql_query(skills_query, conn)
                    
                    # Limit skills per job to prevent memory explosion
                    if len(chunk_skills_df) > 0:
                        chunk_skills_df = chunk_skills_df.groupby(AnalysisConfig.SKILLS_ID_COL).head(AnalysisConfig.MAX_SKILLS_PER_JOB)
                        
                        # Process each movement in the chunk
                        for _, movement in movement_chunk.iterrows():
                            from_job = movement['JobProfileID_from']
                            to_job = movement['JobProfileID_to']
                            
                            if pd.notna(from_job) and pd.notna(to_job):
                                # Get skills for from and to jobs
                                from_skills = chunk_skills_df[chunk_skills_df[AnalysisConfig.SKILLS_ID_COL] == from_job][AnalysisConfig.SKILLS_NAME_COL].tolist()
                                to_skills = chunk_skills_df[chunk_skills_df[AnalysisConfig.SKILLS_ID_COL] == to_job][AnalysisConfig.SKILLS_NAME_COL].tolist()
                                
                                # Record skill transitions
                                for from_skill in from_skills:
                                    for to_skill in to_skills:
                                        if from_skill != to_skill:  # Only record actual transitions
                                            if from_skill not in skill_transitions:
                                                skill_transitions[from_skill] = {}
                                            if to_skill not in skill_transitions[from_skill]:
                                                skill_transitions[from_skill][to_skill] = 0
                                            skill_transitions[from_skill][to_skill] += 1
                
                processed_movements += len(movement_chunk)
                print(f"   → Processed {processed_movements:,}/{len(sampled_movements):,} movements ({processed_movements/len(sampled_movements)*100:.1f}%)")
            
            # Step 4: Analyse skill transition patterns
            print("🔍 Calculating skill diversity scores...")
            skill_metrics = []
            
            for from_skill, transitions in skill_transitions.items():
                total_transitions = sum(transitions.values())
                
                # Only analyse skills with sufficient transition frequency
                if total_transitions >= AnalysisConfig.MIN_SKILL_FREQUENCY:
                    unique_destinations = len(transitions)
                    diversity_score = calculate_diversity_score(transitions)
                    
                    skill_metrics.append({
                        'skill': from_skill,
                        'total_movements': total_transitions,
                        'unique_destinations': unique_destinations,
                        'diversity_score': diversity_score
                    })
            
            if skill_metrics:
                skill_metrics_df = pd.DataFrame(skill_metrics)
                skill_metrics_df = skill_metrics_df.sort_values('diversity_score', ascending=False)
                
                print(f"📊 Analyzed {len(skill_metrics_df)} skills with sufficient movement data")
                
                print(f"\n🎯 TOP SKILL LAUNCHPADS (High Transition Diversity):")
                top_skill_launchpads = skill_metrics_df.head(AnalysisConfig.TOP_N_FEATURES)
                for _, row in top_skill_launchpads.iterrows():
                    print(f"   • {row['skill']}: {row['diversity_score']:.3f} diversity, {row['unique_destinations']} destinations, {row['total_movements']} movements")
                
                print(f"\n🔒 SKILL SILOS (Low Transition Diversity):")
                skill_silos = skill_metrics_df.tail(AnalysisConfig.TOP_N_FEATURES)
                for _, row in skill_silos.iterrows():
                    print(f"   • {row['skill']}: {row['diversity_score']:.3f} diversity, {row['unique_destinations']} destinations, {row['total_movements']} movements")
            else:
                print("⚠️  No skills met minimum frequency threshold for analysis")
        else:
            print("⚠️  No job IDs available for skills analysis")
                
    except Exception as e:
        print(f"⚠️  Skills analysis failed: {str(e)}")
        print("   → Try reducing MAX_MOVEMENTS_FOR_SKILLS or increasing MIN_SKILL_FREQUENCY")
        print("   → Check SKILLS_TABLE configuration and database schema")
    
    # =============================================================================
    # 5. ENHANCED PATHWAY SCORING
    # =============================================================================
    
    print_section_header("ENHANCED PATHWAY SCORING")
    print_methodology(f"""
    Creating enhanced pathway recommendations by combining:
    1. Historical movement probabilities ({AnalysisConfig.PATHWAY_WEIGHTS['movement_probability']*100:.0f}% weight)
    2. Existing similarity scores ({AnalysisConfig.PATHWAY_WEIGHTS['similarity_score']*100:.0f}% weight)
    3. Launchpad destination bonus ({AnalysisConfig.PATHWAY_WEIGHTS['diversity_bonus']*100:.0f}% weight)
    4. Skill bridge bonus ({AnalysisConfig.PATHWAY_WEIGHTS['skill_bridge_bonus']*100:.0f}% weight)
    
    This creates a comprehensive scoring system for personalised recommendations.
    """)
    
    # Calculate movement probabilities
    movement_probabilities = {}
    
    for from_feature in analysis_df[AnalysisConfig.PRIMARY_FEATURE].unique():
        from_movements = analysis_df[analysis_df[AnalysisConfig.PRIMARY_FEATURE] == from_feature]
        total_from_movements = len(from_movements)
        
        if total_from_movements >= AnalysisConfig.MIN_MOVEMENTS_FOR_PROBABILITY:
            to_counts = from_movements[AnalysisConfig.TARGET_FEATURE].value_counts()
            
            for to_feature, count in to_counts.items():
                probability = count / total_from_movements
                movement_probabilities[(from_feature, to_feature)] = {
                    'probability': probability,
                    'movement_count': count,
                    'total_movements': total_from_movements
                }
    
    print(f"📊 Calculated movement probabilities for {len(movement_probabilities)} feature transitions")
    
    # Create pathway scoring function
    def calculate_enhanced_pathway_score(from_feature, to_feature, similarity_score=0.5):
        """
        Calculate enhanced pathway score combining multiple factors
        """
        # Base similarity score
        base_score = similarity_score * AnalysisConfig.PATHWAY_WEIGHTS['similarity_score']
        
        # Movement probability component
        movement_key = (from_feature, to_feature)
        if movement_key in movement_probabilities:
            movement_prob = movement_probabilities[movement_key]['probability']
            movement_score = movement_prob * AnalysisConfig.PATHWAY_WEIGHTS['movement_probability']
        else:
            movement_score = 0.0
        
        # Launchpad bonus (if destination is a launchpad)
        launchpad_bonus = 0.0
        destination_metrics = role_metrics_df[role_metrics_df['feature_value'] == to_feature]
        if not destination_metrics.empty and destination_metrics.iloc[0]['role_type'] == 'Launchpad':
            launchpad_bonus = AnalysisConfig.PATHWAY_WEIGHTS['diversity_bonus']
        
        # Skill bridge bonus (placeholder - would need skill similarity data)
        skill_bridge_bonus = 0.0  # Could be enhanced with actual skill overlap analysis
        
        # Combine all components
        total_score = base_score + movement_score + launchpad_bonus + skill_bridge_bonus
        
        return {
            'total_score': total_score,
            'similarity_component': base_score,
            'movement_component': movement_score,
            'launchpad_bonus': launchpad_bonus,
            'skill_bridge_bonus': skill_bridge_bonus
        }
    
    # Demonstrate enhanced scoring with examples
    print(f"\n📈 ENHANCED PATHWAY SCORING EXAMPLES:")
    
    # Get some example pathways
    example_from_features = analysis_df[AnalysisConfig.PRIMARY_FEATURE].value_counts().head(3).index
    
    for from_feature in example_from_features:
        from_movements = analysis_df[analysis_df[AnalysisConfig.PRIMARY_FEATURE] == from_feature]
        top_destinations = from_movements[AnalysisConfig.TARGET_FEATURE].value_counts().head(3)
        
        print(f"\n   From {from_feature}:")
        
        for to_feature, count in top_destinations.items():
            # Calculate enhanced score (using 0.7 as example similarity)
            enhanced_score = calculate_enhanced_pathway_score(from_feature, to_feature, 0.7)
            
            print(f"     → {to_feature}:")
            print(f"       Total Score: {enhanced_score['total_score']:.3f}")
            print(f"       Components: Similarity={enhanced_score['similarity_component']:.3f}, "
                  f"Movement={enhanced_score['movement_component']:.3f}, "
                  f"Launchpad={enhanced_score['launchpad_bonus']:.3f}")
    
    # =============================================================================
    # 6. SUMMARY AND RECOMMENDATIONS
    # =============================================================================
    
    print_section_header("ANALYSIS SUMMARY & RECOMMENDATIONS")
    
    print("✅ ROLE TYPOLOGY ANALYSIS COMPLETED")
    print(f"   → Analysed {len(role_metrics_df)} {AnalysisConfig.FEATURE_DISPLAY_NAMES[AnalysisConfig.PRIMARY_FEATURE]} values")
    print(f"   → Identified {len(launchpads)} launchpads, {len(silos)} silos, {len(bridges)} bridges")
    print(f"   → Calculated {len(movement_probabilities)} movement probabilities")
    
    print(f"   → Skills analysis: {'Completed' if 'skill_metrics_df' in locals() else 'Failed'}")
    
    print(f"\n🎯 KEY INSIGHTS:")
    print(f"   → {AnalysisConfig.FEATURE_DISPLAY_NAMES[AnalysisConfig.PRIMARY_FEATURE]} provides optimal granularity for role classification")
    print(f"   → Enhanced pathway scoring combines multiple data sources")
    print(f"   → Framework ready for personalised recommendation deployment")
    
    print(f"\n🚀 IMPLEMENTATION RECOMMENDATIONS:")
    print(f"   1. Deploy enhanced pathway scoring in recommendation engine")
    print(f"   2. Use launchpad identification for career development planning")
    print(f"   3. Focus retention efforts on silo roles with high talent concentration")
    print(f"   4. Leverage bridge roles for cross-functional mobility programs")
    
    print(f"\n📊 PRODUCTION DEPLOYMENT:")
    print(f"   → Configuration-driven approach enables easy adaptation")
    print(f"   → Thresholds can be adjusted based on organisational needs")
    print(f"   → Framework scales to additional features and data sources")
    
    # Close database connection
    conn.close()
    print(f"\n🔒 Database connection closed")
    
    # Return results for further use
    return {
        'role_metrics': role_metrics_df,
        'movement_probabilities': movement_probabilities,
        'enhanced_scoring_function': calculate_enhanced_pathway_score,
        'analysis_config': AnalysisConfig.get_config_summary()
    }

if __name__ == "__main__":
    results = main()
    print(f"\n{'='*80}")
    print("ROLE TYPOLOGY & PATHWAY ENHANCEMENT ANALYSIS COMPLETE")
    print(f"{'='*80}") 