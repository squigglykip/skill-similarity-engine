#!/usr/bin/env python3
"""
Enhanced Role Typology Analysis & Pathway Enhancement - V2.0

MAJOR ENHANCEMENTS:
1. Job Profile granularity (715 profiles vs 101 sub-functions)
2. Mobility Score gradient (0-100) instead of binary classification
3. Defining Skills feature based on NAB enterprise rarity
4. Architectural focus (job progression) vs organizational context
5. Multi-level analysis with enhanced insights

This provides granular, actionable career pathway insights focused on job architecture.
"""

import pandas as pd
import numpy as np
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
from pathlib import Path
from scipy import stats
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.cluster import KMeans
import warnings
import gc
import psutil
import time
from typing import Dict, List, Tuple, Any, Optional, Callable

warnings.filterwarnings('ignore')
plt.style.use('default')
sns.set_palette("husl")

# =============================================================================
# ENHANCED CONFIGURATION V2.0
# =============================================================================

DATABASE_FILE = "models/2025-Q3/workforce_intelligence.sqlite"

class EnhancedAnalysisConfigV2:
    """Enhanced configuration with job profile focus and mobility scoring"""
    
    # Database configuration
    DATABASE_PATH = DATABASE_FILE
    
    # PRIMARY ANALYSIS: Job Architecture Dimensions
    ARCHITECTURAL_DIMENSIONS = {
        'job_profile': {
            'primary_feature': 'JobProfileID_from',
            'target_feature': 'JobProfileID_to',
            'display_name': 'Job Profile',
            'context_features': ['from_job_function', 'from_job_sub_function', 'from_management_level'],
            'focus': 'career_progression',
            'defining_skills': True
        },
        'job_sub_function': {
            'primary_feature': 'from_job_sub_function',
            'target_feature': 'to_job_sub_function',
            'display_name': 'Job Sub-Function', 
            'context_features': ['from_job_function', 'from_job_category'],
            'focus': 'career_progression',
            'defining_skills': False
        },
        'management_level': {
            'primary_feature': 'from_management_level',
            'target_feature': 'to_management_level',
            'display_name': 'Management Level',
            'context_features': ['from_job_function'],
            'focus': 'career_progression',
            'defining_skills': False
        }
    }
    
    # CONTEXT: Organizational Placement (supporting information)
    ORGANIZATIONAL_CONTEXT = {
        'division': {
            'feature': 'from_division',
            'target': 'to_division',
            'description': 'Where these career moves happen organizationally'
        },
        'business_unit': {
            'feature': 'from_business_unit', 
            'target': 'to_business_unit',
            'description': 'Business unit context for career moves'
        },
        # Removed salary_group - using job architecture management level instead
    }
    
    # Enhanced feature set (architectural focus)
    MOVEMENT_FEATURES = ['movement_count', 'avg_days_between']
    JOB_ARCHITECTURE_FEATURES = ['JobProfileID_from', 'JobProfileID_to', 'from_job_function', 'from_job_sub_function', 'from_job_category', 'from_management_level']
    ORGANIZATIONAL_CONTEXT_FEATURES = ['from_division', 'from_business_unit']
    
    ALL_FEATURES = MOVEMENT_FEATURES + JOB_ARCHITECTURE_FEATURES + ORGANIZATIONAL_CONTEXT_FEATURES
    
    # Skills analysis configuration
    SKILLS_TABLE = 'job_skills'
    SKILLS_ID_COL = 'JobProfileID'
    SKILLS_NAME_COL = 'Skill_Name'
    MIN_SKILL_FREQUENCY = 3
    SKILLS_CHUNK_SIZE = 2000
    MAX_SKILLS_PER_JOB = 200
    
    # Mobility Score Configuration (0-100 scale)
    MOBILITY_SCORE_WEIGHTS = {
        'diversity_component': 40,      # Shannon diversity (0-40 points)
        'destination_component': 30,    # Unique destinations (0-30 points)
        'volume_component': 20,         # Movement volume (0-20 points) 
        'cross_boundary_component': 10  # Cross-boundary moves (0-10 points)
    }
    
    # Mobility tiers based on score
    MOBILITY_TIERS = {
        (85, 100): "Super Launchpad",
        (70, 84): "Strong Launchpad", 
        (55, 69): "Moderate Launchpad",
        (40, 54): "Standard Mobility",
        (25, 39): "Limited Mobility",
        (0, 24): "Career Silo"
    }
    
    # Defining skills configuration
    DEFINING_SKILLS_CONFIG = {
        'max_prevalence_rare': 5.0,     # <5% = rare skill
        'max_prevalence_uncommon': 20.0, # 5-20% = uncommon skill
        'max_prevalence_common': 50.0,   # 20-50% = common skill
        'top_n_defining': 5,              # Show top 5 defining skills per role
        'min_jobs_for_analysis': 1        # Minimum jobs for analysis (was 10, now 1 for full coverage)
    }
    
    # Enhanced pathway scoring weights
    PATHWAY_WEIGHTS = {
        'movement_probability': 0.35,
        'similarity_score': 0.25,
        'mobility_bonus': 0.20,          # Bonus for high mobility target roles
        'skill_match_bonus': 0.10,       # Bonus for high defining skill overlap
        'architectural_alignment': 0.10  # Bonus for logical architectural progression
    }
    
    # Optimization settings
    MEMORY_LIMIT_MB = 4000
    CHUNK_SIZE_MOVEMENTS = 5000
    PARALLEL_WORKERS = 4
    MIN_MOVEMENTS_FOR_PROBABILITY = 10

# =============================================================================
# ENHANCED UTILITY FUNCTIONS
# =============================================================================

def get_memory_usage():
    """Get current memory usage in MB"""
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024

def trigger_garbage_collection():
    """Trigger garbage collection and return collected objects"""
    return gc.collect()

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

def print_metric_definitions(metric_type):
    """Print clear definitions for different metric types"""
    definitions = {
        'mobility_score': """
📖 MOBILITY SCORE DEFINITIONS:
• Mobility Score (0-100): Overall career mobility potential combining multiple factors
• Diversity Component (0-40): Shannon diversity of transition destinations (higher = more varied career paths)
• Destinations Component (0-30): Number of unique destination roles (higher = more career options)
• Volume Component (0-20): Total movement frequency (higher = more active role transitions)
• Cross-boundary Component (0-10): Rate of moves across divisions/categories (higher = more boundary-crossing)

🏆 MOBILITY TIERS:
• Super Launchpad (85-100): Exceptional mobility with diverse, high-volume transitions
• Strong Launchpad (70-84): High mobility with multiple pathway options
• Moderate Launchpad (55-69): Good mobility with solid transition opportunities
• Standard Mobility (40-54): Average mobility following typical patterns
• Limited Mobility (25-39): Below-average mobility with fewer options
• Career Silo (0-24): Very limited mobility, concentrated in specific roles
        """,
        
        'pathway_scoring': """
📖 PATHWAY SCORING DEFINITIONS:
• Total Score (0-1): Combined pathway recommendation strength from all components
• Movement Component (35% weight): Historical probability of this specific transition occurring
• Similarity Component (25% weight): Role compatibility based on job architecture alignment
• Mobility Bonus (20% weight): Bonus for transitioning to high-mobility destination roles
• Skill Match Bonus (10% weight): Bonus for overlapping defining skills between roles
• Architectural Alignment (10% weight): Bonus for logical progression within job functions

💡 INTERPRETATION:
• Scores >0.7: Highly recommended pathways with strong historical precedent
• Scores 0.5-0.7: Good pathways with moderate support and opportunity
• Scores 0.3-0.5: Possible pathways requiring more development or networking
• Scores <0.3: Challenging pathways with limited historical precedent
        """,
        
        'skill_rarity': """
📖 SKILL RARITY DEFINITIONS:
• Prevalence Percentage: What % of NAB's job profiles require this skill
• Rarity Category: Classification based on enterprise-wide distribution
  - Rare (<5%): Highly specialised skills found in few roles
  - Uncommon (5-20%): Specialised skills with moderate distribution
  - Common (20-50%): Widely applicable skills across many roles
  - Universal (>50%): Core skills required by most positions
• Defining Skills: The 5 rarest skills that best characterise each job profile
• Rarity Score: Inverse measure of prevalence (higher = more distinctive/valuable)
        """,
        
        'skill_mobility': """
📖 SKILL MOBILITY DEFINITIONS:
• Skill Mobility Score (0-100): How effectively a skill facilitates transitions to other skills
• Skill Launchpads: Skills that open pathways to many other skills (high mobility)
• Skill Silos: Skills that lead to limited other skills (low mobility, specialised)
• Skill Diversity: How varied the destination skills are from this starting skill
• Cross-Category Rate: How often this skill leads to skills in different categories
• Bridge Skills: Skills that connect different skill domains/categories

🌉 SKILL MOBILITY TIERS:
• Super Launchpad Skills (85-100): Gateway skills opening many career paths
• Strong Launchpad Skills (70-84): Versatile skills with multiple transition options
• Moderate Launchpad Skills (55-69): Good foundational skills for skill development
• Standard Mobility Skills (40-54): Average transferability to other skills
• Limited Mobility Skills (25-39): Somewhat specialised with fewer connections
• Skill Silos (0-24): Highly specialised skills with limited transferability
        """
    }
    
    if metric_type in definitions:
        print(definitions[metric_type])

def get_human_readable_name(job_profile_id, defining_skills_dict, fallback_name=None):
    """Get human-readable name for job profile, with fallback options"""
    if job_profile_id in defining_skills_dict:
        return defining_skills_dict[job_profile_id]['job_profile']
    elif fallback_name:
        return fallback_name
    else:
        return str(job_profile_id)

def calculate_percentile_rank(value, all_values):
    """Calculate percentile rank for a value within a distribution"""
    if len(all_values) == 0:
        return 50.0
    rank = stats.percentileofscore(all_values, value, kind='rank')
    return round(rank, 1)

def format_mobility_score_with_context(row, all_scores, defining_skills_dict):
    """Format mobility score with percentile rank and context"""
    job_id = row['feature_value']
    score = row['mobility_score']
    tier = row['mobility_tier']
    
    # Get human-readable name
    job_name = get_human_readable_name(job_id, defining_skills_dict)
    if len(job_name) > 50:
        job_name = job_name[:47] + "..."
    
    # Calculate percentile rank
    percentile = calculate_percentile_rank(score, all_scores)
    
    # Get components for detailed breakdown
    components = row['mobility_components']
    
    return {
        'job_name': job_name,
        'score': score,
        'tier': tier,
        'percentile': percentile,
        'components': components,
        'context': f"Ranks in top {100-percentile:.0f}% of all roles" if percentile > 50 else f"Below median (bottom {percentile:.0f}%)"
    }

def print_memory_usage():
    """Print current memory usage"""
    memory_mb = get_memory_usage()
    print(f"💾 Memory Usage: {memory_mb:.1f} MB")

def chunk_dataframe(df, chunk_size):
    """Simple DataFrame chunking function"""
    for i in range(0, len(df), chunk_size):
        yield df.iloc[i:i + chunk_size]

def calculate_diversity_score(transition_counts):
    """
    Calculate Shannon diversity index for transition patterns.
    Higher score = more diverse transitions (higher mobility)
    Lower score = concentrated transitions (lower mobility)
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

def normalize_column_names(df):
    """Normalize column names to lowercase with underscores for consistent access"""
    column_mapping = {}
    for col in df.columns:
        normalized = col.lower().replace(' ', '_').replace('-', '_')
        column_mapping[col] = normalized
    
    df_normalized = df.rename(columns=column_mapping)
    
    print(f"📋 Column name normalization:")
    for original, normalized in column_mapping.items():
        if original != normalized:
            print(f"   → '{original}' → '{normalized}'")
    
    return df_normalized

# =============================================================================
# ENHANCED DATA LOADING FUNCTIONS
# =============================================================================

def load_database():
    """Connect to database from configured path"""
    try:
        conn = sqlite3.connect(EnhancedAnalysisConfigV2.DATABASE_PATH)
        print(f"✅ Connected to database: {EnhancedAnalysisConfigV2.DATABASE_PATH}")
        return conn
    except sqlite3.OperationalError as e:
        raise FileNotFoundError(f"Could not connect to database: {EnhancedAnalysisConfigV2.DATABASE_PATH}. Error: {str(e)}")

def load_movement_data_from_database(conn):
    """Load movement data from the movement_fact table in the database"""
    try:
        print(f"📁 Loading movement data from database table: movement_fact")
        
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
        """
        
        movement_df = pd.read_sql_query(query, conn)
        movement_df = normalize_column_names(movement_df)
        
        print(f"✅ Successfully loaded {len(movement_df):,} records from movement_fact table")
        
        if 'movement_year' in movement_df.columns:
            min_year = movement_df['movement_year'].min()
            max_year = movement_df['movement_year'].max()
            print(f"📅 Data range: {min_year} - {max_year}")
        
        return movement_df
    except Exception as e:
        raise RuntimeError(f"Failed to load movement data from database: {str(e)}")

def calculate_aggressive_recency_weight(movement_date, reference_date=None, decay_rate=0.4):
    """
    Aggressive decay for fast-changing banking environment
    decay_rate=0.4 means each year back loses 60% of relevance
    """
    from datetime import datetime
    
    if reference_date is None:
        reference_date = datetime.now()
    
    # Convert to pandas datetime for consistent handling
    movement_date = pd.to_datetime(movement_date)
    reference_date = pd.to_datetime(reference_date)
    
    # Calculate years difference
    days_diff = (reference_date - movement_date).days
    years_ago = days_diff / 365.25
    
    weight = decay_rate ** years_ago
    
    return max(weight, 0.05)  # Minimum weight threshold

def create_clean_movement_dataset_v2(movement_df, jobs_df):
    """
    Conservative null exclusion with steep recency weighting
    Only keep movements between current job profiles
    """
    from datetime import datetime
    
    original_count = len(movement_df)
    
    # Step 1: Only keep movements where both positions exist in current job arch
    print(f"   → Initial records: {len(movement_df):,}")
    
    # Check if JobProfileID columns exist
    required_cols = ['JobProfileID_from', 'JobProfileID_to']
    missing_cols = [col for col in required_cols if col not in movement_df.columns]
    if missing_cols:
        print(f"   ⚠️  Missing columns: {missing_cols}")
        print(f"   → Available columns: {list(movement_df.columns)}")
        # Skip job profile filtering if columns don't exist
        clean_df = movement_df.copy()
    else:
        clean_df = movement_df.dropna(subset=['JobProfileID_from', 'JobProfileID_to'])
        print(f"   → After dropping null JobProfileIDs: {len(clean_df):,}")
        
        current_job_profiles = set(jobs_df['JobProfileID'].unique())
        print(f"   → Current job profiles available: {len(current_job_profiles):,}")
        
        before_filter = len(clean_df)
        clean_df = clean_df[
            clean_df['JobProfileID_from'].isin(current_job_profiles) &
            clean_df['JobProfileID_to'].isin(current_job_profiles)
        ]
        print(f"   → After job profile filtering: {len(clean_df):,} (removed {before_filter - len(clean_df):,})")
    
    # Step 2: Apply aggressive recency weighting
    # Convert movement_date if needed
    if 'movement_date' in clean_df.columns:
        # Ensure movement_date is datetime
        clean_df = clean_df.copy()
        clean_df['movement_date'] = pd.to_datetime(clean_df['movement_date'])
        clean_df['recency_weight'] = clean_df['movement_date'].apply(
            calculate_aggressive_recency_weight
        )
    elif 'movement_year' in clean_df.columns:
        # Create date from year and calculate weights
        clean_df = clean_df.copy()
        clean_df['movement_date'] = pd.to_datetime(clean_df['movement_year'], format='%Y')
        # Calculate recency weights as float values
        recency_weights = []
        for date_val in clean_df['movement_date']:
            weight = calculate_aggressive_recency_weight(date_val)
            recency_weights.append(weight)
        clean_df['recency_weight'] = recency_weights
    else:
        print("⚠️  No date column found, using uniform weights")
        clean_df = clean_df.copy()
        clean_df['recency_weight'] = 1.0
    
    # Step 3: Filter out movements with negligible weight
    # Ensure recency_weight is numeric before comparison
    clean_df['recency_weight'] = pd.to_numeric(clean_df['recency_weight'], errors='coerce')
    clean_df = clean_df[clean_df['recency_weight'] >= 0.01]
    
    # Simple retention reporting by year
    if 'movement_year' in movement_df.columns:
        print("   → Data retention by year:")
        for year in sorted(movement_df['movement_year'].unique()):
            original_year = len(movement_df[movement_df['movement_year'] == year])
            clean_year = len(clean_df[clean_df['movement_year'] == year])
            retention = (clean_year / original_year * 100) if original_year > 0 else 0
            print(f"     {year}: {retention:.1f}% retained")
    
    total_retention = len(clean_df) / original_count * 100
    print(f"   → Overall retention: {total_retention:.1f}%")
    
    return clean_df

def enhanced_data_enrichment_v2(movement_df, conn):
    """Enhanced data enrichment with job profile focus and recency weighting"""
    print("🔄 Enhanced data enrichment V2.0 with job profile focus and recency weighting...")
    
    # Load reference data
    jobs_df = pd.read_sql_query("SELECT * FROM jobs", conn)
    positions_df = pd.read_sql_query("SELECT * FROM positions", conn)
    
    # Try to load workforce context if available
    try:
        workforce_df = pd.read_sql_query("SELECT * FROM workforce_context", conn)
        print(f"🏢 Loaded workforce context: {len(workforce_df):,} records")
    except:
        workforce_df = None
        print("⚠️  Workforce context table not available")
    
    print(f"🏢 Loaded jobs data: {len(jobs_df):,} job profiles")
    print(f"🏢 Loaded positions data: {len(positions_df):,} position records")
    
    # Create enhanced position mapping with organizational context
    position_mapping_columns = ['Position Number', 'JobProfileID']
    
    # Add organizational context columns if available
    org_context_columns = []
    if 'Division' in positions_df.columns:
        org_context_columns.append('Division')
        print(f"   → Found Division → organizational context")
    if 'Business_Unit' in positions_df.columns:
        org_context_columns.append('Business_Unit')
        print(f"   → Found Business_Unit → organizational context")
    elif 'Business Unit' in positions_df.columns:
        positions_df['Business_Unit'] = positions_df['Business Unit']
        org_context_columns.append('Business_Unit')
        print(f"   → Found Business Unit → organizational context")
    
    # Management level is now handled through job architecture enrichment
    # (removed salary group as it's less reliable than job architecture management level)
    
    position_mapping_columns.extend(org_context_columns)
    print(f"   → Enhanced position mapping: {position_mapping_columns}")
    
    # Create enhanced position mapping and deduplicate to fix cartesian products
    enhanced_position_mapping = positions_df[position_mapping_columns].copy()
    
    # Fix cartesian product issue by deduplicating positions
    original_positions = len(enhanced_position_mapping)
    duplicate_positions = enhanced_position_mapping['Position Number'].duplicated().sum()
    
    if duplicate_positions > 0:
        print(f"   ⚠️  Found {duplicate_positions:,} duplicate position numbers - deduplicating...")
        
        # Deduplicate by keeping first occurrence of each position number
        # This preserves the most common job profile for each position
        enhanced_position_mapping = enhanced_position_mapping.drop_duplicates(
            subset=['Position Number'], 
            keep='first'
        )
        
        deduplicated_positions = len(enhanced_position_mapping)
        print(f"   → Deduplicated from {original_positions:,} to {deduplicated_positions:,} positions")
        print(f"   → Removed {original_positions - deduplicated_positions:,} duplicate position records")
    else:
        print(f"   ✅ No duplicate position numbers found")
    
    # Data type conversion
    enhanced_position_mapping['Position Number'] = enhanced_position_mapping['Position Number'].astype(str)
    movement_df['from_position'] = movement_df['from_position'].astype(str)
    movement_df['to_position'] = movement_df['to_position'].astype(str)
    
    # Chunked enrichment process
    enriched_chunks = []
    chunk_size = EnhancedAnalysisConfigV2.CHUNK_SIZE_MOVEMENTS
    
    print(f"   → Processing {len(movement_df):,} records in chunks...")
    
    for i, chunk in enumerate(chunk_dataframe(movement_df, chunk_size)):
        # Enrich with FROM position context
        chunk_enriched = chunk.merge(
            enhanced_position_mapping,
            left_on='from_position',
            right_on='Position Number',
            how='left',
            suffixes=('', '_from')
        ).drop('Position Number', axis=1, errors='ignore')
        
        # Enrich with TO position context
        chunk_enriched = chunk_enriched.merge(
            enhanced_position_mapping,
            left_on='to_position',
            right_on='Position Number',
            how='left',
            suffixes=('_from', '_to')
        ).drop('Position Number', axis=1, errors='ignore')
        
        # Enrich with job architecture (PRIMARY FOCUS)
        chunk_enriched = chunk_enriched.merge(
            jobs_df[['JobProfileID', 'JobFunction', 'JobSubFunction', 'ManagementLevel', 'JobCategory']],
            left_on='JobProfileID_from',
            right_on='JobProfileID',
            how='left',
            suffixes=('', '_job_from')
        ).drop('JobProfileID', axis=1, errors='ignore')
        
        chunk_enriched = chunk_enriched.merge(
            jobs_df[['JobProfileID', 'JobFunction', 'JobSubFunction', 'ManagementLevel', 'JobCategory']],
            left_on='JobProfileID_to',
            right_on='JobProfileID',
            how='left',
            suffixes=('_from', '_to')
        ).drop('JobProfileID', axis=1, errors='ignore')
        
        # Standardize column names for architectural features
        rename_mapping = {
            'JobFunction_from': 'from_job_function',
            'JobSubFunction_from': 'from_job_sub_function',
            'JobCategory_from': 'from_job_category',
            'ManagementLevel_from': 'from_management_level',
            'JobFunction_to': 'to_job_function',
            'JobSubFunction_to': 'to_job_sub_function',
            'JobCategory_to': 'to_job_category',
            'ManagementLevel_to': 'to_management_level',
        }
        
        # Add organizational context mappings (CONTEXT ONLY)
        if 'Division_from' in chunk_enriched.columns:
            rename_mapping['Division_from'] = 'from_division'
        if 'Division_to' in chunk_enriched.columns:
            rename_mapping['Division_to'] = 'to_division'
        if 'Business_Unit_from' in chunk_enriched.columns:
            rename_mapping['Business_Unit_from'] = 'from_business_unit'
        if 'Business_Unit_to' in chunk_enriched.columns:
            rename_mapping['Business_Unit_to'] = 'to_business_unit'
        # Removed salary group mappings - using job architecture management level instead
        
        chunk_enriched = chunk_enriched.rename(columns=rename_mapping)
        enriched_chunks.append(chunk_enriched)
    
    # Combine all chunks
    enriched_df = pd.concat(enriched_chunks, ignore_index=True)
    
    # Cleanup
    del enriched_chunks
    trigger_garbage_collection()
    
    print(f"✅ Enhanced enriched dataset V2.0: {len(enriched_df):,} movement records")
    print_memory_usage()
    
    return enriched_df

# =============================================================================
# SKILL MOBILITY ANALYSIS
# =============================================================================

def calculate_skill_mobility_scores(conn, defining_skills_per_job):
    """Calculate mobility scores for skills using same methodology as job profiles"""
    print("🎯 Calculating skill mobility scores (launchpads vs silos)...")
    
    try:
        # Get skill transition data by analyzing movements between roles with different skill sets
        skill_transition_query = """
        SELECT 
            mf.movement_year,
            p_from.JobProfileID as JobProfileID_from,
            p_to.JobProfileID as JobProfileID_to,
            mf.movement_count
        FROM movement_fact mf
        JOIN positions p_from ON mf.from_position = p_from.[Position Number]
        JOIN positions p_to ON mf.to_position = p_to.[Position Number]
        WHERE mf.movement_year >= 2020
        AND p_from.JobProfileID IS NOT NULL 
        AND p_to.JobProfileID IS NOT NULL
        """
        
        movement_df = pd.read_sql_query(skill_transition_query, conn)
        
        # Get job-skill mappings
        job_skills_query = """
        SELECT js.JobProfileID, js.Skill_ID, s.Skill_Name, s.Category
        FROM job_skills js
        JOIN skills s ON js.Skill_ID = s.Skill_ID
        """
        job_skills_df = pd.read_sql_query(job_skills_query, conn)
        
        # MEMORY OPTIMIZATION: Focus on skills that are actually in use
        print(f"   → Processing {len(movement_df):,} movements and {len(job_skills_df):,} job-skill mappings")
        
        # Get all job profiles that actually appear in movements (skills in active use)
        active_job_profiles = set(movement_df['JobProfileID_from'].unique()) | set(movement_df['JobProfileID_to'].unique())
        
        # Filter job-skills to only those in active job profiles
        active_job_skills = job_skills_df[job_skills_df['JobProfileID'].isin(active_job_profiles)].copy()
        
        print(f"   → Focusing on {len(active_job_profiles):,} active job profiles")
        print(f"   → Analyzing {len(active_job_skills):,} skills in active use")
        
        # Get skills that actually have movement data
        skills_in_use = active_job_skills['Skill_ID'].unique()
        
        if len(skills_in_use) == 0:
            print(f"   ⚠️  No skills found in movement data")
            return {}
        
        # For each skill, analyze how it facilitates transitions to other skills
        skill_mobility_data = {}
        
        print(f"   → Calculating mobility scores for {len(skills_in_use):,} active skills...")
        
        # Process skills in batches to manage memory
        batch_size = 100
        for i in range(0, len(skills_in_use), batch_size):
            skill_batch = skills_in_use[i:i + batch_size]
            
            for skill_id in skill_batch:
                skill_info = active_job_skills[active_job_skills['Skill_ID'] == skill_id].iloc[0]
                skill_name = skill_info['Skill_Name']
                
                # Get job profiles that have this skill
                jobs_with_skill = active_job_skills[active_job_skills['Skill_ID'] == skill_id]['JobProfileID'].unique()
                
                # Get movements FROM jobs with this skill
                from_movements = movement_df[movement_df['JobProfileID_from'].isin(jobs_with_skill)]
                
                if len(from_movements) == 0:
                    continue
                
                # Get skills in destination jobs
                destination_job_skills = from_movements.merge(
                    active_job_skills[['JobProfileID', 'Skill_ID', 'Category']], 
                    left_on='JobProfileID_to', 
                    right_on='JobProfileID', 
                    how='inner'
                )
                
                # Filter out the same skill (we want transitions TO other skills)
                destination_other_skills = destination_job_skills[destination_job_skills['Skill_ID'] != skill_id]
                
                if len(destination_other_skills) > 5:  # Minimum transitions for analysis
                    # Calculate diversity of destination skills
                    destination_skills = destination_other_skills['Skill_ID'].value_counts()
                    diversity_score = calculate_diversity_score(destination_skills.to_dict())
                    
                    # Count unique destination skills
                    unique_destinations = len(destination_skills)
                    
                    # Calculate total transition volume (weight by movement count)
                    total_movements = destination_other_skills['movement_count'].sum()
                    
                    # Calculate cross-category transitions
                    source_category = skill_info['Category']
                    cross_category_moves = destination_other_skills[
                        destination_other_skills['Category'] != source_category
                    ]['movement_count'].sum()
                    cross_category_rate = cross_category_moves / total_movements if total_movements > 0 else 0
                    
                    # Calculate skill mobility score using same components as job mobility
                    skill_metrics = {
                        'diversity_score': diversity_score,
                        'unique_destinations': unique_destinations,
                        'total_movements': total_movements,
                        'cross_category_rate': cross_category_rate,
                        'cross_division_rate': 0  # Not applicable for skills
                    }
                    
                    mobility_analysis = calculate_mobility_score(skill_metrics)
                    
                    skill_mobility_data[skill_id] = {
                        'skill_name': skill_name,
                        'mobility_score': mobility_analysis['mobility_score'],
                        'mobility_tier': mobility_analysis['mobility_tier'],
                        'mobility_components': mobility_analysis['components'],
                        'total_transitions': total_movements,
                        'unique_skill_destinations': unique_destinations,
                        'diversity_score': diversity_score,
                        'cross_category_rate': cross_category_rate,
                        'top_destination_skills': destination_skills.head(3).to_dict()
                    }
        
        print(f"   → Calculated mobility scores for {len(skill_mobility_data):,} skills")
        
        return skill_mobility_data
        
    except Exception as e:
        print(f"   ⚠️  Skill mobility analysis failed: {str(e)}")
        return {}

def display_skill_mobility_insights(skill_mobility_data):
    """Display skill mobility insights with launchpad/silo classification"""
    if not skill_mobility_data:
        print("   ⚠️  No skill mobility data available")
        return
    
    print_metric_definitions('skill_mobility')
    
    # Convert to DataFrame for analysis
    skill_mobility_df = pd.DataFrame.from_dict(skill_mobility_data, orient='index')
    skill_mobility_df = skill_mobility_df.sort_values('mobility_score', ascending=False)
    
    # Show distribution
    tier_distribution = skill_mobility_df['mobility_tier'].value_counts()
    print(f"\n   📊 SKILL MOBILITY DISTRIBUTION:")
    for tier, count in tier_distribution.items():
        percentage = count / len(skill_mobility_df) * 100
        avg_score = skill_mobility_df[skill_mobility_df['mobility_tier'] == tier]['mobility_score'].mean()
        print(f"      {tier}: {count} skills ({percentage:.1f}%) - Average Score: {avg_score:.1f}")
    
    # Show top skill launchpads
    print(f"\n   🚀 TOP SKILL LAUNCHPADS (Career Bridge Skills):")
    top_skills = skill_mobility_df.head(10)
    for i, (skill_id, row) in enumerate(top_skills.iterrows(), 1):
        print(f"      {i}. {row['skill_name']}: {row['mobility_score']:.1f} ({row['mobility_tier']})")
        print(f"         Leads to {row['unique_skill_destinations']} different skills, {row['total_transitions']} transitions")
    
    # Show skill silos
    print(f"\n   🔒 SKILL SILOS (Specialised/Isolated Skills):")
    bottom_skills = skill_mobility_df.tail(10)
    for i, (skill_id, row) in enumerate(bottom_skills.iterrows(), 1):
        print(f"      {i}. {row['skill_name']}: {row['mobility_score']:.1f} ({row['mobility_tier']})")
        print(f"         Limited transitions: {row['unique_skill_destinations']} destinations, {row['total_transitions']} moves")
    
    return skill_mobility_df

# =============================================================================
# DEFINING SKILLS ANALYSIS
# =============================================================================

def calculate_enterprise_skill_rarity(conn):
    """Calculate skill rarity scores based on NAB enterprise job profile distribution"""
    print("🎯 Calculating enterprise-wide skill rarity scores...")
    
    # Get total job profiles in enterprise
    total_job_profiles_query = "SELECT COUNT(DISTINCT JobProfileID) as total FROM jobs"
    total_jobs = pd.read_sql_query(total_job_profiles_query, conn).iloc[0]['total']
    
    print(f"   → Total job profiles in enterprise: {total_jobs:,}")
    
    # Calculate skill prevalence across job profiles
    skill_rarity_query = f"""
    SELECT 
        s.Skill_ID,
        s.Skill_Name,
        s.Category,
        s.SkillType,
        COUNT(DISTINCT js.JobProfileID) as jobs_using_skill,
        COUNT(DISTINCT js.JobProfileID) * 100.0 / {total_jobs} as prevalence_percentage,
        {total_jobs} - COUNT(DISTINCT js.JobProfileID) as rarity_score
    FROM skills s
    JOIN job_skills js ON s.Skill_ID = js.Skill_ID  
    GROUP BY s.Skill_ID, s.Skill_Name, s.Category, s.SkillType
    HAVING COUNT(DISTINCT js.JobProfileID) >= {EnhancedAnalysisConfigV2.DEFINING_SKILLS_CONFIG['min_jobs_for_analysis']}
    ORDER BY prevalence_percentage ASC
    """
    
    skill_rarity_df = pd.read_sql_query(skill_rarity_query, conn)
    
    # Handle any null values in prevalence_percentage
    skill_rarity_df['prevalence_percentage'].fillna(100.0, inplace=True)  # Unknown = universal
    skill_rarity_df['rarity_score'].fillna(0.0, inplace=True)  # Unknown = lowest rarity
    
    # Categorize skills by rarity (with null safety)
    def categorize_rarity(x):
        if pd.isna(x) or x is None:
            return 'Universal'
        elif x < EnhancedAnalysisConfigV2.DEFINING_SKILLS_CONFIG['max_prevalence_rare']:
            return 'Rare'
        elif x < EnhancedAnalysisConfigV2.DEFINING_SKILLS_CONFIG['max_prevalence_uncommon']:
            return 'Uncommon' 
        elif x < EnhancedAnalysisConfigV2.DEFINING_SKILLS_CONFIG['max_prevalence_common']:
            return 'Common'
        else:
            return 'Universal'
    
    skill_rarity_df['rarity_category'] = skill_rarity_df['prevalence_percentage'].apply(categorize_rarity)
    
    print(f"   → Calculated rarity for {len(skill_rarity_df):,} skills")
    
    # Show rarity distribution
    rarity_dist = skill_rarity_df['rarity_category'].value_counts()
    print(f"   → Rarity distribution:")
    for category, count in rarity_dist.items():
        percentage = count / len(skill_rarity_df) * 100
        print(f"      {category}: {count:,} skills ({percentage:.1f}%)")
    
    return skill_rarity_df

def identify_defining_skills_per_job(conn, skill_rarity_df):
    """Identify defining skills for each job profile based on rarity"""
    print("🔍 Identifying defining skills per job profile...")
    
    # Get job skills data
    job_defining_skills_query = """
    SELECT 
        js.JobProfileID,
        j.JobProfile,
        s.Skill_Name,
        s.Category
    FROM job_skills js
    JOIN jobs j ON js.JobProfileID = j.JobProfileID
    JOIN skills s ON js.Skill_ID = s.Skill_ID
    """
    
    job_skills_base = pd.read_sql_query(job_defining_skills_query, conn)
    
    # Merge with rarity data
    job_skills_enhanced = job_skills_base.merge(
        skill_rarity_df[['Skill_Name', 'prevalence_percentage', 'rarity_category', 'rarity_score']],
        on='Skill_Name',
        how='left',
        suffixes=('', '_calc')
    )
    
    # Ensure the _calc columns exist (handle cases where suffixes weren't added)
    if 'prevalence_percentage_calc' not in job_skills_enhanced.columns:
        if 'prevalence_percentage' in job_skills_enhanced.columns:
            job_skills_enhanced['prevalence_percentage_calc'] = job_skills_enhanced['prevalence_percentage']
        else:
            job_skills_enhanced['prevalence_percentage_calc'] = 100.0
    
    if 'rarity_category_calc' not in job_skills_enhanced.columns:
        if 'rarity_category' in job_skills_enhanced.columns:
            job_skills_enhanced['rarity_category_calc'] = job_skills_enhanced['rarity_category']
        else:
            job_skills_enhanced['rarity_category_calc'] = 'Universal'
    
    if 'rarity_score_calc' not in job_skills_enhanced.columns:
        if 'rarity_score' in job_skills_enhanced.columns:
            job_skills_enhanced['rarity_score_calc'] = job_skills_enhanced['rarity_score']
        else:
            job_skills_enhanced['rarity_score_calc'] = 0.0
    
    # Fill any missing rarity values with defaults
    job_skills_enhanced['prevalence_percentage_calc'].fillna(100.0, inplace=True)  # Unknown skills = common
    job_skills_enhanced['rarity_category_calc'].fillna('Universal', inplace=True)
    job_skills_enhanced['rarity_score_calc'].fillna(0.0, inplace=True)  # Unknown skills = lowest rarity
    
    # For each job profile, get top defining skills (rarest skills)
    defining_skills_per_job = {}
    
    for job_id in job_skills_enhanced['JobProfileID'].unique():
        job_skills = job_skills_enhanced[job_skills_enhanced['JobProfileID'] == job_id]
        
        # Filter out any remaining null values and sort by rarity score (highest = rarest = most defining)
        job_skills_clean = job_skills.dropna(subset=['rarity_score_calc'])
        
        if len(job_skills_clean) > 0:
            top_defining = job_skills_clean.nlargest(
                min(EnhancedAnalysisConfigV2.DEFINING_SKILLS_CONFIG['top_n_defining'], len(job_skills_clean)), 
                'rarity_score_calc'
            )
        else:
            # Fallback if no valid rarity scores
            top_defining = job_skills.head(EnhancedAnalysisConfigV2.DEFINING_SKILLS_CONFIG['top_n_defining'])
        
        defining_skills_per_job[job_id] = {
            'job_profile': job_skills.iloc[0]['JobProfile'] if len(job_skills) > 0 else 'Unknown',
            'defining_skills': top_defining[['Skill_Name', 'prevalence_percentage_calc', 'rarity_category_calc']].to_dict('records'),
            'total_skills': len(job_skills),
            'rare_skills_count': len(job_skills[job_skills['rarity_category_calc'] == 'Rare'])
        }
    
    print(f"   → Identified defining skills for {len(defining_skills_per_job):,} job profiles")
    
    return defining_skills_per_job

# =============================================================================
# ENHANCED MOBILITY SCORING
# =============================================================================

def calculate_mobility_score(role_metrics):
    """Calculate 0-100 mobility score with component breakdown"""
    
    # Component 1: Diversity Score (0-40 points)
    diversity_component = role_metrics['diversity_score'] * EnhancedAnalysisConfigV2.MOBILITY_SCORE_WEIGHTS['diversity_component']
    
    # Component 2: Destination Variety (0-30 points)
    # Scale: 10+ destinations = max points
    destination_component = min(
        role_metrics['unique_destinations'] / 10 * EnhancedAnalysisConfigV2.MOBILITY_SCORE_WEIGHTS['destination_component'], 
        EnhancedAnalysisConfigV2.MOBILITY_SCORE_WEIGHTS['destination_component']
    )
    
    # Component 3: Movement Volume (0-20 points)  
    # Scale: 100+ movements = max points
    volume_component = min(
        role_metrics['total_movements'] / 100 * EnhancedAnalysisConfigV2.MOBILITY_SCORE_WEIGHTS['volume_component'],
        EnhancedAnalysisConfigV2.MOBILITY_SCORE_WEIGHTS['volume_component']
    )
    
    # Component 4: Cross-Boundary Movements (0-10 points)
    cross_boundary_rate = role_metrics.get('cross_division_rate', role_metrics.get('cross_category_rate', 0))
    cross_boundary_component = cross_boundary_rate * EnhancedAnalysisConfigV2.MOBILITY_SCORE_WEIGHTS['cross_boundary_component']
    
    # Total mobility score
    total_mobility_score = diversity_component + destination_component + volume_component + cross_boundary_component
    
    # Determine mobility tier
    mobility_tier = get_mobility_tier(total_mobility_score)
    
    return {
        'mobility_score': round(total_mobility_score, 1),
        'mobility_tier': mobility_tier,
        'components': {
            'diversity': round(diversity_component, 1),
            'destinations': round(destination_component, 1),
            'volume': round(volume_component, 1),
            'cross_boundary': round(cross_boundary_component, 1)
        }
    }

def get_mobility_tier(score):
    """Convert mobility score to descriptive tier"""
    for (min_score, max_score), tier_name in EnhancedAnalysisConfigV2.MOBILITY_TIERS.items():
        if min_score <= score <= max_score:
            return tier_name
    return "Unknown"

def calculate_enhanced_role_metrics_v2(feature_groups: List[Tuple[str, pd.DataFrame]], dimension_config: Dict) -> List[Dict]:
    """Calculate enhanced role metrics with mobility scoring and recency weighting"""
    results = []
    
    for feature_value, feature_movements in feature_groups:
        # Basic transition patterns with recency weighting
        target_feature = dimension_config['target_feature']
        
        # Apply recency weighting if available
        if 'recency_weight' in feature_movements.columns:
            # Weight the transitions by recency
            weighted_transitions = feature_movements.groupby(target_feature)['recency_weight'].sum()
            transitions = weighted_transitions.sort_values(ascending=False)
            total_movements = feature_movements['recency_weight'].sum()
        else:
            transitions = feature_movements[target_feature].value_counts()
            total_movements = len(feature_movements)
        
        unique_destinations = len(transitions)
        
        # Calculate diversity score
        diversity_score = calculate_diversity_score(transitions.to_dict())
        
        # Calculate cross-category movements (architectural boundaries) with weighting
        cross_category_rate = 0.0
        if 'from_job_category' in feature_movements.columns and 'to_job_category' in feature_movements.columns:
            if 'recency_weight' in feature_movements.columns:
                cross_category_moves = feature_movements[
                    feature_movements['from_job_category'] != feature_movements['to_job_category']
                ]['recency_weight'].sum()
                cross_category_rate = cross_category_moves / total_movements if total_movements > 0 else 0.0
            else:
                cross_category_moves = (feature_movements['from_job_category'] != feature_movements['to_job_category']).sum()
                cross_category_rate = cross_category_moves / total_movements if total_movements > 0 else 0.0
        
        # Calculate cross-divisional movements (organizational context) with weighting
        cross_division_rate = 0.0
        if 'from_division' in feature_movements.columns and 'to_division' in feature_movements.columns:
            if 'recency_weight' in feature_movements.columns:
                cross_division_moves = feature_movements[
                    feature_movements['from_division'] != feature_movements['to_division']
                ]['recency_weight'].sum()
                cross_division_rate = cross_division_moves / total_movements if total_movements > 0 else 0.0
            else:
                cross_division_moves = (feature_movements['from_division'] != feature_movements['to_division']).sum()
                cross_division_rate = cross_division_moves / total_movements if total_movements > 0 else 0.0
        
        # Calculate average movement characteristics with recency weighting
        if 'recency_weight' in feature_movements.columns:
            # Weighted averages
            total_weight = feature_movements['recency_weight'].sum()
            if total_weight > 0:
                avg_movement_count = (feature_movements['movement_count'] * feature_movements['recency_weight']).sum() / total_weight if 'movement_count' in feature_movements.columns else 0
                avg_days_between = (feature_movements['avg_days_between'] * feature_movements['recency_weight']).sum() / total_weight if 'avg_days_between' in feature_movements.columns else 0
            else:
                avg_movement_count = 0
                avg_days_between = 0
        else:
            avg_movement_count = feature_movements['movement_count'].mean() if 'movement_count' in feature_movements.columns else 0
            avg_days_between = feature_movements['avg_days_between'].mean() if 'avg_days_between' in feature_movements.columns else 0
        
        # Enhanced mobility scoring
        role_metrics = {
            'diversity_score': diversity_score,
            'unique_destinations': unique_destinations,
            'total_movements': total_movements,
            'cross_category_rate': cross_category_rate,
            'cross_division_rate': cross_division_rate
        }
        
        mobility_analysis = calculate_mobility_score(role_metrics)
        
        # Store enhanced metrics
        results.append({
            'feature_value': feature_value,
            'total_movements': total_movements,
            'unique_destinations': unique_destinations,
            'diversity_score': diversity_score,
            'cross_category_rate': cross_category_rate,
            'cross_division_rate': cross_division_rate,
            'avg_movement_count': avg_movement_count,
            'avg_days_between': avg_days_between,
            'top_destination': transitions.index[0] if len(transitions) > 0 else None,
            'top_destination_rate': transitions.iloc[0] / total_movements if len(transitions) > 0 else 0.0,
            'dimension': dimension_config['display_name'],
            'mobility_score': mobility_analysis['mobility_score'],
            'mobility_tier': mobility_analysis['mobility_tier'],
            'mobility_components': mobility_analysis['components']
        })
    
    return results

# =============================================================================
# ENHANCED PATHWAY SCORING V2
# =============================================================================

def calculate_enhanced_pathway_probabilities_v2(analysis_df: pd.DataFrame, dimension_config: Dict) -> Dict:
    """Calculate movement probabilities for enhanced pathway scoring"""
    print(f"📊 Calculating enhanced movement probabilities for {dimension_config['display_name']}...")
    
    primary_feature = dimension_config['primary_feature']
    target_feature = dimension_config['target_feature']
    
    unique_features = analysis_df[primary_feature].unique()
    movement_probabilities = {}
    
    for feature in unique_features:
        feature_movements = analysis_df[analysis_df[primary_feature] == feature]
        total_movements = len(feature_movements)
        
        if total_movements >= EnhancedAnalysisConfigV2.MIN_MOVEMENTS_FOR_PROBABILITY:
            to_counts = feature_movements[target_feature].value_counts()
            
            for to_feature, count in to_counts.items():
                probability = count / total_movements
                
                # Enhanced context for architectural progression
                avg_days = feature_movements['avg_days_between'].mean() if 'avg_days_between' in feature_movements.columns else 0
                avg_count = feature_movements['movement_count'].mean() if 'movement_count' in feature_movements.columns else 0
                
                # Architectural alignment score (same job function = good alignment)
                architectural_alignment = 0.0
                if 'from_job_function' in feature_movements.columns and 'to_job_function' in feature_movements.columns:
                    same_function_moves = (feature_movements['from_job_function'] == feature_movements['to_job_function']).sum()
                    architectural_alignment = same_function_moves / total_movements
                
                movement_probabilities[(feature, to_feature)] = {
                    'probability': probability,
                    'movement_count': count,
                    'total_movements': total_movements,
                    'avg_days_between': avg_days,
                    'avg_movement_count': avg_count,
                    'architectural_alignment': architectural_alignment
                }
    
    print(f"   → Calculated {len(movement_probabilities):,} enhanced movement probabilities")
    return movement_probabilities

def create_enhanced_pathway_scoring_function_v2(movement_probabilities: Dict, role_metrics_df: pd.DataFrame, defining_skills: Optional[Dict] = None) -> Callable:
    """Create enhanced pathway scoring function with architectural focus"""
    
    def calculate_enhanced_pathway_score_v2(from_feature, to_feature, similarity_score=0.5, dimension='job_profile'):
        """Calculate enhanced pathway score with mobility and skills bonuses"""
        
        # Base similarity score
        base_score = similarity_score * EnhancedAnalysisConfigV2.PATHWAY_WEIGHTS['similarity_score']
        
        # Movement probability component
        movement_key = (from_feature, to_feature)
        movement_score = 0.0
        architectural_alignment_score = 0.0
        
        if movement_key in movement_probabilities:
            movement_data = movement_probabilities[movement_key]
            movement_prob = movement_data['probability']
            movement_score = movement_prob * EnhancedAnalysisConfigV2.PATHWAY_WEIGHTS['movement_probability']
            
            # Architectural alignment bonus
            arch_alignment = movement_data.get('architectural_alignment', 0.0)
            architectural_alignment_score = arch_alignment * EnhancedAnalysisConfigV2.PATHWAY_WEIGHTS['architectural_alignment']
        
        # Mobility bonus (high mobility target roles get bonus)
        mobility_bonus = 0.0
        destination_metrics = role_metrics_df[role_metrics_df['feature_value'] == to_feature]
        if not destination_metrics.empty:
            target_mobility_score = destination_metrics.iloc[0]['mobility_score']
            # Normalize mobility score to 0-1 for bonus calculation
            mobility_bonus = (target_mobility_score / 100) * EnhancedAnalysisConfigV2.PATHWAY_WEIGHTS['mobility_bonus']
        
        # Skill match bonus (if defining skills available)
        skill_match_bonus = 0.0
        if defining_skills and from_feature in defining_skills and to_feature in defining_skills:
            # Calculate skill overlap between source and target roles
            source_skills = set([skill['Skill_Name'] for skill in defining_skills[from_feature]['defining_skills']])
            target_skills = set([skill['Skill_Name'] for skill in defining_skills[to_feature]['defining_skills']])
            
            if len(source_skills) > 0 and len(target_skills) > 0:
                overlap = len(source_skills.intersection(target_skills))
                max_possible = len(source_skills.union(target_skills))
                skill_overlap_ratio = overlap / max_possible if max_possible > 0 else 0
                skill_match_bonus = skill_overlap_ratio * EnhancedAnalysisConfigV2.PATHWAY_WEIGHTS['skill_match_bonus']
        
        # Combine all components
        total_score = base_score + movement_score + mobility_bonus + skill_match_bonus + architectural_alignment_score
        
        return {
            'total_score': total_score,
            'similarity_component': base_score,
            'movement_component': movement_score,
            'mobility_bonus': mobility_bonus,
            'skill_match_bonus': skill_match_bonus,
            'architectural_alignment': architectural_alignment_score,
            'dimension': dimension
        }
    
    return calculate_enhanced_pathway_score_v2

# =============================================================================
# MAIN ENHANCED ANALYSIS FUNCTION V2
# =============================================================================

def get_database_scope_metrics(conn):
    """Get dynamic database scope metrics instead of hardcoded values"""
    
    metrics = {}
    
    # Get job profile count
    try:
        job_profile_count = pd.read_sql_query("SELECT COUNT(DISTINCT JobProfileID) as count FROM jobs", conn).iloc[0]['count']
        metrics['job_profiles'] = job_profile_count
    except:
        metrics['job_profiles'] = 'Unknown'
    
    # Get job sub-function count  
    try:
        sub_function_count = pd.read_sql_query("SELECT COUNT(DISTINCT JobSubFunction) as count FROM jobs", conn).iloc[0]['count']
        metrics['job_sub_functions'] = sub_function_count
    except:
        metrics['job_sub_functions'] = 'Unknown'
    
    # Get total movement records
    try:
        movement_count = pd.read_sql_query("SELECT COUNT(*) as count FROM movement_fact", conn).iloc[0]['count']
        metrics['total_movements'] = movement_count
    except:
        metrics['total_movements'] = 'Unknown'
    
    # Get unique skills count
    try:
        skills_count = pd.read_sql_query("SELECT COUNT(DISTINCT Skill_ID) as count FROM skills", conn).iloc[0]['count']
        metrics['total_skills'] = skills_count
    except:
        metrics['total_skills'] = 'Unknown'
    
    # Get position count
    try:
        position_count = pd.read_sql_query("SELECT COUNT(DISTINCT [Position Number]) as count FROM positions", conn).iloc[0]['count']
        metrics['total_positions'] = position_count
    except:
        metrics['total_positions'] = 'Unknown'
    
    # Get date range
    try:
        date_range = pd.read_sql_query("SELECT MIN(movement_year) as min_year, MAX(movement_year) as max_year FROM movement_fact", conn)
        metrics['date_range'] = f"{date_range.iloc[0]['min_year']} - {date_range.iloc[0]['max_year']}"
    except:
        metrics['date_range'] = 'Unknown'
    
    return metrics

def main():
    """Main enhanced analysis function V2.0"""
    
    print_section_header(
        "ENHANCED ROLE TYPOLOGY ANALYSIS & PATHWAY ENHANCEMENT V2.0",
        "Job Profile Focus • Mobility Scoring • Defining Skills • Architectural Progression"
    )
    
    # Connect to database first to get scope metrics
    conn = load_database()
    scope_metrics = get_database_scope_metrics(conn)
    
    print("🚀 ENHANCED ANALYSIS FEATURES V2.0:")
    print(f"   → Job Profile granularity ({scope_metrics['job_profiles']:,} profiles vs {scope_metrics['job_sub_functions']:,} sub-functions)")
    print("   → Mobility Score gradient (0-100) replacing binary classification")
    print("   → Defining Skills feature based on NAB enterprise rarity")
    print("   → Architectural focus (career progression) vs organizational context")
    print("   → Multi-level analysis with enhanced pathway insights")
    print(f"   → Dataset scope: {scope_metrics['total_movements']:,} movements, {scope_metrics['total_positions']:,} positions, {scope_metrics['total_skills']:,} skills")
    print(f"   → Time range: {scope_metrics['date_range']}")
    print_memory_usage()
    
    # =============================================================================
    # 1. ENHANCED DATA LOADING AND PREPARATION V2
    # =============================================================================
    
    print_section_header("ENHANCED DATA LOADING AND PREPARATION V2.0")
    print_methodology("""
    Enhanced data loading with job profile focus and temporal handling:
    1. Load movement data from database (temporal aggregations preserved)
    2. Load job architecture, positions, and workforce context
    3. Enrich movements with full job profile and organizational context
    4. Apply recency weighting (40% decay rate - banking environment changes fast)
    5. Filter to current job profiles only (recommendations for existing roles)
    6. Deduplicate position mappings to prevent cartesian products
    7. Memory-efficient processing with enhanced context preservation
    """)
    
    # Load data (conn already established above for scope metrics)
    movement_df = load_movement_data_from_database(conn)
    
    # Load jobs data for cleaning
    jobs_df = pd.read_sql_query("SELECT * FROM jobs", conn)
    
    enriched_df = enhanced_data_enrichment_v2(movement_df, conn)
    
    # Cleanup
    del movement_df
    trigger_garbage_collection()
    
    print(f"📊 Enhanced dataset V2.0: {len(enriched_df):,} enriched movement records")
    print(f"📅 Date range: {enriched_df['movement_year'].min()} - {enriched_df['movement_year'].max()}")
    
    # Apply data cleaning with recency weighting
    print("🔄 Applying data cleaning with recency weighting...")
    enriched_df = create_clean_movement_dataset_v2(enriched_df, jobs_df)
    
    print(f"📊 Cleaned dataset V2.0: {len(enriched_df):,} weighted movement records")
    
    # Check available features
    available_features = [col for col in EnhancedAnalysisConfigV2.ALL_FEATURES if col in enriched_df.columns]
    print(f"🔍 Available enhanced features ({len(available_features)}): {available_features}")
    
    print_memory_usage()
    
    # =============================================================================
    # 2. ENTERPRISE SKILL RARITY ANALYSIS
    # =============================================================================
    
    print_section_header("ENTERPRISE SKILL RARITY ANALYSIS")
    print_methodology(f"""
    Calculating defining skills based on NAB enterprise rarity:
    1. Calculate skill prevalence across all {scope_metrics['job_profiles']:,} job profiles
    2. Categorize skills by rarity (Rare <5%, Uncommon 5-20%, Common 20-50%, Universal >50%)
    3. Identify top 5 defining skills per job profile (rarest skills)
    4. Create skill-based differentiation profiles for career guidance
    """)
    
    try:
        # Calculate enterprise-wide skill rarity
        skill_rarity_df = calculate_enterprise_skill_rarity(conn)
        
        # Identify defining skills per job profile
        defining_skills_per_job = identify_defining_skills_per_job(conn, skill_rarity_df)
        
        # Print skill rarity definitions
        print_metric_definitions('skill_rarity')
        
        print(f"\n✅ ENTERPRISE SKILL RARITY ANALYSIS COMPLETED")
        print(f"   → {len(skill_rarity_df):,} skills analyzed across NAB enterprise")
        print(f"   → {len(defining_skills_per_job):,} job profiles with defining skill profiles")
        
        # Enhanced skill distribution summary
        print(f"\n📊 SKILL RARITY DISTRIBUTION ACROSS NAB:")
        rarity_dist = skill_rarity_df['rarity_category'].value_counts()
        total_skills = len(skill_rarity_df)
        for category, count in rarity_dist.items():
            percentage = count / total_skills * 100
            print(f"   • {category}: {count:,} skills ({percentage:.1f}%)")
        
        # Add skill mobility analysis
        print(f"\n🌉 SKILL MOBILITY ANALYSIS (Launchpads vs Silos):")
        skill_mobility_data = calculate_skill_mobility_scores(conn, defining_skills_per_job)
        skill_mobility_df = display_skill_mobility_insights(skill_mobility_data)
        
        # Show example defining skills with enhanced context
        print(f"\n🎯 DEFINING SKILLS EXAMPLES (What Makes These Roles Unique):")
        example_jobs = list(defining_skills_per_job.keys())[:3]
        for job_id in example_jobs:
            job_info = defining_skills_per_job[job_id]
            print(f"\n   📋 {job_info['job_profile']}:")
            print(f"      Skill Profile: {job_info['total_skills']} total skills, {job_info['rare_skills_count']} rare/specialised")
            print(f"      Top Defining Skills (What Makes This Role Distinctive):")
            for i, skill in enumerate(job_info['defining_skills'][:3], 1):
                rarity_context = ""
                if skill['prevalence_percentage_calc'] < 1:
                    rarity_context = "extremely rare"
                elif skill['prevalence_percentage_calc'] < 5:
                    rarity_context = "highly specialised"
                elif skill['prevalence_percentage_calc'] < 20:
                    rarity_context = "specialised"
                else:
                    rarity_context = "common"
                
                print(f"        {i}. {skill['Skill_Name']}: {skill['prevalence_percentage_calc']:.1f}% of roles ({rarity_context})")
        
    except Exception as e:
        print(f"   ⚠️  Skill rarity analysis failed: {str(e)}")
        skill_rarity_df = pd.DataFrame()
        defining_skills_per_job = {}
    
    # =============================================================================
    # 3. MULTI-DIMENSIONAL ROLE TYPOLOGY ANALYSIS WITH MOBILITY SCORING
    # =============================================================================
    
    print_section_header("MULTI-DIMENSIONAL ROLE ANALYSIS WITH MOBILITY SCORING")
    print_methodology(f"""
    Multi-dimensional role analysis with Mobility Score (0-100) and recency weighting:
    1. Job Profile Analysis (PRIMARY: {scope_metrics['job_profiles']:,} current job profiles)
    2. Job Sub-Function Analysis (SECONDARY: {scope_metrics['job_sub_functions']:,} broader patterns)
    3. Management Level Analysis (PROGRESSION: career advancement)
    4. Mobility Score calculation with recency-weighted transitions
    5. Architectural progression focus vs organizational context
    6. Temporal decay applied (recent moves weighted higher)
    """)
    
    all_role_metrics = []
    all_movement_probabilities = {}
    dimension_results = {}
    
    # Analyze each architectural dimension
    for dimension_name, dimension_config in EnhancedAnalysisConfigV2.ARCHITECTURAL_DIMENSIONS.items():
        print(f"\n🔍 ANALYZING ARCHITECTURAL DIMENSION: {dimension_config['display_name']}")
        
        primary_feature = dimension_config['primary_feature']
        target_feature = dimension_config['target_feature']
        
        # Check if features are available
        if primary_feature not in enriched_df.columns or target_feature not in enriched_df.columns:
            print(f"   ⚠️  Features not available: {primary_feature}, {target_feature}")
            continue
        
        # Filter to complete records for this dimension
        dimension_df = enriched_df.dropna(subset=[primary_feature, target_feature])
        print(f"   → Analysis dataset: {len(dimension_df):,} complete records")
        
        if len(dimension_df) == 0:
            print(f"   ⚠️  No complete records for {dimension_config['display_name']}")
            continue
        
        # Prepare feature groups
        unique_features = dimension_df[primary_feature].unique()
        feature_groups = []
        
        for feature_value in unique_features:
            feature_movements = dimension_df[dimension_df[primary_feature] == feature_value]
            feature_groups.append((feature_value, feature_movements))
        
        # Calculate enhanced role metrics with mobility scoring
        print(f"   → Processing {len(feature_groups)} {dimension_config['display_name']} values...")
        role_metrics = calculate_enhanced_role_metrics_v2(feature_groups, dimension_config)
        
        # Convert to DataFrame
        role_metrics_df = pd.DataFrame(role_metrics)
        role_metrics_df = role_metrics_df.sort_values('mobility_score', ascending=False)
        
        # Print metric definitions before showing results
        print_metric_definitions('mobility_score')
        
        # Display mobility score results with enhanced context
        mobility_tier_summary = role_metrics_df['mobility_tier'].value_counts()
        print(f"\n   📊 MOBILITY SCORE DISTRIBUTION FOR {dimension_config['display_name'].upper()}:")
        for tier, count in mobility_tier_summary.items():
            percentage = count / len(role_metrics_df) * 100
            avg_score = role_metrics_df[role_metrics_df['mobility_tier'] == tier]['mobility_score'].mean()
            print(f"      {tier}: {count} roles ({percentage:.1f}%) - Average Score: {avg_score:.1f}")
        
        # Show top mobility examples with enhanced formatting
        all_scores = role_metrics_df['mobility_score'].tolist()
        top_mobility = role_metrics_df.head(5)
        low_mobility = role_metrics_df.tail(5)
        
        print(f"\n   🚀 HIGHEST MOBILITY ROLES (Top Career Launchpads):")
        for _, row in top_mobility.iterrows():
            formatted = format_mobility_score_with_context(row, all_scores, defining_skills_per_job)
            print(f"      • {formatted['job_name']}")
            print(f"        Score: {formatted['score']:.1f} ({formatted['tier']}) - {formatted['context']}")
            print(f"        Components: Diversity={formatted['components']['diversity']:.1f}, "
                  f"Destinations={formatted['components']['destinations']:.1f}, "
                  f"Volume={formatted['components']['volume']:.1f}, "
                  f"Cross-boundary={formatted['components']['cross_boundary']:.1f}")
        
        print(f"\n   🔒 LOWEST MOBILITY ROLES (Career Development Focus Areas):")
        for _, row in low_mobility.iterrows():
            formatted = format_mobility_score_with_context(row, all_scores, defining_skills_per_job)
            print(f"      • {formatted['job_name']}")
            print(f"        Score: {formatted['score']:.1f} ({formatted['tier']}) - {formatted['context']}")
        
        # Calculate movement probabilities for this dimension
        movement_probabilities = calculate_enhanced_pathway_probabilities_v2(dimension_df, dimension_config)
        
        # Store results
        all_role_metrics.extend(role_metrics)
        all_movement_probabilities[dimension_name] = movement_probabilities
        dimension_results[dimension_name] = {
            'role_metrics_df': role_metrics_df,
            'movement_probabilities': movement_probabilities,
            'config': dimension_config
        }
    
    # =============================================================================
    # 4. ENHANCED PATHWAY SCORING SYSTEM V2
    # =============================================================================
    
    print_section_header("ENHANCED PATHWAY SCORING SYSTEM V2.0")
    print_methodology(f"""
    Enhanced pathway scoring with architectural focus:
    1. Movement probability analysis ({EnhancedAnalysisConfigV2.PATHWAY_WEIGHTS['movement_probability']*100:.0f}% weight)
    2. Similarity score integration ({EnhancedAnalysisConfigV2.PATHWAY_WEIGHTS['similarity_score']*100:.0f}% weight)
    3. Mobility Score bonuses ({EnhancedAnalysisConfigV2.PATHWAY_WEIGHTS['mobility_bonus']*100:.0f}% weight)
    4. Skill match bonuses ({EnhancedAnalysisConfigV2.PATHWAY_WEIGHTS['skill_match_bonus']*100:.0f}% weight)
    5. Architectural alignment scores ({EnhancedAnalysisConfigV2.PATHWAY_WEIGHTS['architectural_alignment']*100:.0f}% weight)
    """)
    
    # Create enhanced scoring functions for each dimension
    enhanced_scoring_functions = {}
    
    for dimension_name, dimension_data in dimension_results.items():
        role_metrics_df = dimension_data['role_metrics_df']
        movement_probabilities = dimension_data['movement_probabilities']
        
        scoring_function = create_enhanced_pathway_scoring_function_v2(
            movement_probabilities, 
            role_metrics_df, 
            defining_skills_per_job
        )
        
        enhanced_scoring_functions[dimension_name] = scoring_function
        
        # Print pathway scoring definitions
        print_metric_definitions('pathway_scoring')
        
        print(f"\n   📈 PATHWAY SCORING EXAMPLES FOR {dimension_data['config']['display_name'].upper()}:")
        
        # Get example pathways
        primary_feature = dimension_data['config']['primary_feature']
        target_feature = dimension_data['config']['target_feature']
        
        # Filter data for this dimension
        dimension_df = enriched_df.dropna(subset=[primary_feature, target_feature])
        
        if len(dimension_df) > 0:
            example_features = dimension_df[primary_feature].value_counts().head(3).index
            
            for from_feature in example_features:
                from_movements = dimension_df[dimension_df[primary_feature] == from_feature]
                top_destinations = from_movements[target_feature].value_counts().head(3)
                
                # Get human-readable name for source role
                from_display = get_human_readable_name(from_feature, defining_skills_per_job)
                if len(from_display) > 45:
                    from_display = from_display[:42] + "..."
                
                print(f"\n      🎯 FROM: {from_display}")
                
                for to_feature, count in top_destinations.items():
                    enhanced_score = scoring_function(from_feature, to_feature, 0.7, dimension_name)
                    
                    # Get human-readable name for destination role
                    to_display = get_human_readable_name(to_feature, defining_skills_per_job)
                    if len(to_display) > 40:
                        to_display = to_display[:37] + "..."
                    
                    # Interpret the score
                    score_interpretation = ""
                    total_score = enhanced_score['total_score']
                    if total_score > 0.7:
                        score_interpretation = "🌟 Highly Recommended"
                    elif total_score > 0.5:
                        score_interpretation = "✅ Good Pathway"
                    elif total_score > 0.3:
                        score_interpretation = "⚠️ Possible (Development Needed)"
                    else:
                        score_interpretation = "🔴 Challenging Transition"
                    
                    print(f"         → TO: {to_display}")
                    print(f"           Score: {total_score:.3f} ({score_interpretation})")
                    print(f"           Movement Probability: {enhanced_score['movement_component']:.3f} | "
                          f"Similarity: {enhanced_score['similarity_component']:.3f} | "
                          f"Mobility Bonus: {enhanced_score['mobility_bonus']:.3f}")
                    print(f"           Historical Moves: {count} people made this transition")
    
    # =============================================================================
    # 5. ENHANCED SUMMARY AND STRATEGIC RECOMMENDATIONS V2
    # =============================================================================
    
    print_section_header("ENHANCED ANALYSIS SUMMARY & STRATEGIC RECOMMENDATIONS V2.0")
    
    print("✅ ENHANCED MULTI-DIMENSIONAL ANALYSIS V2.0 COMPLETED")
    print(f"   → Analyzed {len(EnhancedAnalysisConfigV2.ARCHITECTURAL_DIMENSIONS)} architectural dimensions")
    print(f"   → Processed {len(all_role_metrics)} total role classifications with Mobility Scores")
    print(f"   → Enterprise skills analysis: {'Completed' if defining_skills_per_job else 'Attempted'}")
    print(f"   → Created {len(enhanced_scoring_functions)} enhanced scoring functions")
    
    print_memory_usage()
    
    print(f"\n🚀 V2.0 ENHANCEMENTS IMPLEMENTED:")
    print(f"   → Job Profile granularity ({scope_metrics['job_profiles']:,} profiles vs {scope_metrics['job_sub_functions']:,} sub-functions)")
    print(f"   → Mobility Score gradient (0-100) replacing binary classification")
    print(f"   → Defining Skills feature with NAB enterprise rarity scoring")
    print(f"   → Architectural progression focus vs organizational context")
    print(f"   → Enhanced pathway scoring with skill matching and mobility bonuses")
    print(f"   → Temporal recency weighting with 40% decay rate for banking environment")
    
    print(f"\n🎯 KEY ACTIONABLE INSIGHTS:")
    
    # Calculate summary statistics
    all_mobility_scores = []
    high_mobility_roles = []
    silo_roles = []
    
    for dimension_name, dimension_data in dimension_results.items():
        if dimension_name == 'job_profile':  # Focus on job profile insights
            role_metrics_df = dimension_data['role_metrics_df']
            all_mobility_scores.extend(role_metrics_df['mobility_score'].tolist())
            
            # Get high mobility and silo roles
            high_mobility = role_metrics_df[role_metrics_df['mobility_score'] >= 70]
            silo_roles_df = role_metrics_df[role_metrics_df['mobility_score'] < 25]
            
            for _, row in high_mobility.iterrows():
                job_name = get_human_readable_name(row['feature_value'], defining_skills_per_job)
                high_mobility_roles.append(job_name)
            
            for _, row in silo_roles_df.iterrows():
                job_name = get_human_readable_name(row['feature_value'], defining_skills_per_job)
                silo_roles.append(job_name)
    
    print(f"   → GRANULAR GUIDANCE: {scope_metrics['job_profiles']:,} job profiles with individual mobility scores")
    print(f"   → CAREER LAUNCHPADS: {len(high_mobility_roles)} roles identified as strong mobility platforms")
    print(f"   → DEVELOPMENT FOCUS: {len(silo_roles)} roles requiring targeted career development support")
    print(f"   → SKILL INTELLIGENCE: {scope_metrics['total_skills']:,} skills categorised by enterprise rarity")
    print(f"   → ARCHITECTURAL FOCUS: Career progression patterns separated from organisational placement")
    print(f"   → TEMPORAL RELEVANCE: Recent movement patterns weighted 60% higher than historical")
    
    print(f"\n📋 IMMEDIATE ACTIONABLE RECOMMENDATIONS:")
    print(f"   🎯 INDIVIDUAL CAREER COUNSELLING:")
    print(f"      • Use mobility scores (0-100) to set realistic progression expectations")
    print(f"      • Focus skill development on rare/defining skills for target roles")
    print(f"      • Prioritise pathways with scores >0.5 (good probability of success)")
    
    print(f"   🏢 ORGANISATIONAL TALENT STRATEGY:")
    print(f"      • Deploy high-mobility roles as talent development accelerators")
    print(f"      • Design intervention programs for Career Silo roles (score <25)")
    print(f"      • Leverage defining skills insights for targeted recruitment")
    
    print(f"   📊 MOBILITY TIER INTERVENTIONS:")
    print(f"      • Super/Strong Launchpads (70-100): Use as talent development hubs")
    print(f"      • Moderate Launchpads (55-69): Standard progression support")
    print(f"      • Limited Mobility/Silos (0-39): Enhanced development programs needed")
    
    if high_mobility_roles:
        print(f"\n🚀 TOP CAREER LAUNCHPAD ROLES TO LEVERAGE:")
        for i, role in enumerate(high_mobility_roles[:5], 1):
            print(f"      {i}. {role}")
    
    if silo_roles:
        print(f"\n🔒 CAREER DEVELOPMENT PRIORITY ROLES:")
        for i, role in enumerate(silo_roles[:5], 1):
            print(f"      {i}. {role}")
    
    # Final cleanup
    trigger_garbage_collection()
    conn.close()
    print(f"\n🔒 Database connection closed")
    print_memory_usage()
    
    # Return comprehensive results
    return {
        'dimension_results': dimension_results,
        'all_role_metrics': all_role_metrics,
        'all_movement_probabilities': all_movement_probabilities,
        'skill_rarity_analysis': skill_rarity_df,
        'defining_skills_per_job': defining_skills_per_job,
        'enhanced_scoring_functions': enhanced_scoring_functions,
        'analysis_config': EnhancedAnalysisConfigV2.__dict__
    }

if __name__ == "__main__":
    start_time = time.time()
    results = main()
    end_time = time.time()
    
    print(f"\n{'='*80}")
    print("ENHANCED ROLE TYPOLOGY & PATHWAY ENHANCEMENT ANALYSIS V2.0 COMPLETE")
    print(f"Total execution time: {end_time - start_time:.2f} seconds")
    print(f"{'='*80}") 