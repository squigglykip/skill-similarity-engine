#!/usr/bin/env python3
"""
SKILLS INTELLIGENCE ENGINE V2 - Clean Architecture
================================================================

Focused implementation based on refined conceptual framework:
- Skill Rarity Intelligence (Job Archetype Definition)
- Rarity-Weighted Job Similarity (Strategic Foundation)
- Descriptive Intelligence for Architectural Thinking

Philosophy: Provide skill architecture maps, not strategic value judgments

Usage:
    python skill_intelligence_engine_v2.py
"""

import pandas as pd
import numpy as np
import sqlite3
import warnings
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Set, Any

warnings.filterwarnings('ignore')

# =============================================================================
# CONFIGURATION
# =============================================================================

DATABASE_FILE = "models/2025-Q3/workforce_intelligence.sqlite"

class SkillIntelligenceConfig:
    """Configuration for Skills Intelligence Engine V2"""
    
    DATABASE_PATH = DATABASE_FILE
    
    # Rarity thresholds for skill categorisation
    RARITY_THRESHOLDS = {
        'rare': 5.0,        # <5% = rare (defining skills)
        'uncommon': 20.0,   # 5-20% = uncommon
        'common': 50.0,     # 20-50% = common
        # >50% = universal
    }

# =============================================================================
# CORE FUNCTIONS
# =============================================================================

def connect_database():
    """Connect to the workforce intelligence database"""
    try:
        conn = sqlite3.connect(SkillIntelligenceConfig.DATABASE_PATH)
        print(f"✅ Connected to database: {SkillIntelligenceConfig.DATABASE_PATH}")
        return conn
    except sqlite3.OperationalError as e:
        raise FileNotFoundError(f"Could not connect to database: {e}")

def load_skill_universe(conn) -> pd.DataFrame:
    """
    Load active skill universe with prevalence calculations
    
    Only includes skills that are actually used in job profiles (appear in job_skills table)
    
    Returns:
        DataFrame with active skills, prevalence percentages, and rarity categories
    """
    print("📚 Loading active skill universe...")
    
    # Get total job profiles for prevalence calculation
    total_profiles_query = "SELECT COUNT(DISTINCT JobProfileID) as total FROM jobs"
    total_profiles = pd.read_sql_query(total_profiles_query, conn).iloc[0]['total']
    
    # Calculate skill prevalence across job profiles - ONLY for skills that are actually used
    skill_prevalence_query = f"""
    SELECT 
        s.Skill_ID,
        s.Skill_Name,
        s.Category,
        s.SkillType,
        COUNT(DISTINCT js.JobProfileID) as job_profiles_with_skill,
        COUNT(DISTINCT js.JobProfileID) * 100.0 / {total_profiles} as prevalence_percentage
    FROM skills s
    INNER JOIN job_skills js ON s.Skill_ID = js.Skill_ID
    GROUP BY s.Skill_ID, s.Skill_Name, s.Category, s.SkillType
    ORDER BY prevalence_percentage ASC
    """
    
    skill_universe = pd.read_sql_query(skill_prevalence_query, conn)
    
    # Categorise by rarity
    skill_universe['rarity_category'] = skill_universe['prevalence_percentage'].apply(categorise_rarity)
    
    print(f"   → Loaded {len(skill_universe):,} active skills (skills used in job profiles)")
    print(f"   → Total job profiles: {total_profiles:,}")
    
    # Show rarity distribution
    rarity_dist = skill_universe['rarity_category'].value_counts()
    print(f"   → Rarity distribution:")
    for category, count in rarity_dist.items():
        percentage = (count / len(skill_universe)) * 100
        print(f"      • {category}: {count:,} skills ({percentage:.1f}%)")
    
    return skill_universe

def categorise_rarity(prevalence_percentage: float) -> str:
    """Categorise skill by rarity based on prevalence"""
    if prevalence_percentage < SkillIntelligenceConfig.RARITY_THRESHOLDS['rare']:
        return 'Rare'
    elif prevalence_percentage < SkillIntelligenceConfig.RARITY_THRESHOLDS['uncommon']:
        return 'Uncommon'
    elif prevalence_percentage < SkillIntelligenceConfig.RARITY_THRESHOLDS['common']:
        return 'Common'
    else:
        return 'Universal'

def identify_defining_skills_with_context(conn, skill_universe: pd.DataFrame, rarity_threshold: float = 5.0) -> pd.DataFrame:
    """
    Identify defining skills with job profile context (rare skills that characterise specific role archetypes)
    
    Args:
        conn: Database connection
        skill_universe: DataFrame with skill prevalence data
        rarity_threshold: Percentage threshold for "rare" classification
    
    Returns:
        DataFrame with defining skills and the job profiles they define
    """
    print(f"🎯 Identifying defining skills with job profile context (prevalence < {rarity_threshold}%)...")
    
    # Get rare skills
    rare_skills = skill_universe[
        skill_universe['prevalence_percentage'] < rarity_threshold
    ]['Skill_ID'].tolist()
    
    if len(rare_skills) == 0:
        print("   → No defining skills found")
        return pd.DataFrame()
    
    # Get job profiles that use these rare skills
    rare_skills_list = "', '".join(rare_skills)
    defining_skills_context_query = f"""
    SELECT 
        s.Skill_ID,
        s.Skill_Name,
        s.Category,
        s.SkillType,
        j.JobProfileID,
        j.JobProfile,
        j.JobFunction,
        j.JobCategory,
        COUNT(DISTINCT js2.JobProfileID) as total_profiles_with_skill
    FROM skills s
    JOIN job_skills js ON s.Skill_ID = js.Skill_ID
    JOIN jobs j ON js.JobProfileID = j.JobProfileID
    JOIN job_skills js2 ON s.Skill_ID = js2.Skill_ID
    WHERE s.Skill_ID IN ('{rare_skills_list}')
    GROUP BY s.Skill_ID, s.Skill_Name, s.Category, s.SkillType, j.JobProfileID, j.JobProfile, j.JobFunction, j.JobCategory
    ORDER BY total_profiles_with_skill ASC, s.Skill_Name, j.JobProfile
    """
    
    defining_skills_with_context = pd.read_sql_query(defining_skills_context_query, conn)
    
    # Add prevalence percentage from skill_universe
    defining_skills_with_context = defining_skills_with_context.merge(
        skill_universe[['Skill_ID', 'prevalence_percentage', 'rarity_category']], 
        on='Skill_ID', 
        how='left'
    )
    
    print(f"   → Found {len(rare_skills):,} defining skills")
    print(f"   → Mapped to {len(defining_skills_with_context):,} skill-job profile combinations")
    
    # Show examples
    if len(defining_skills_with_context) > 0:
        most_rare = defining_skills_with_context.iloc[0]
        print(f"   → Most rare: {most_rare['Skill_Name']} ({most_rare['prevalence_percentage']:.2f}%) defines {most_rare['JobProfile']}")
    
    return defining_skills_with_context

def load_job_skill_matrix(conn) -> Tuple[pd.DataFrame, Dict[str, Set[str]]]:
    """
    Load job-skill relationships as matrix for similarity calculations
    
    Returns:
        Tuple of (job_skills_df, job_to_skills_dict)
    """
    print("🔗 Loading job-skill relationships...")
    
    job_skills_query = """
    SELECT 
        j.JobProfileID,
        j.JobProfile,
        js.Skill_ID,
        s.Skill_Name
    FROM jobs j
    JOIN job_skills js ON j.JobProfileID = js.JobProfileID
    JOIN skills s ON js.Skill_ID = s.Skill_ID
    ORDER BY j.JobProfileID, s.Skill_Name
    """
    
    job_skills_df = pd.read_sql_query(job_skills_query, conn)
    
    # Create job-to-skills mapping for efficient similarity calculations
    job_to_skills = {}
    for job_id in job_skills_df['JobProfileID'].unique():
        job_skills = set(job_skills_df[job_skills_df['JobProfileID'] == job_id]['Skill_Name'])
        job_to_skills[job_id] = job_skills
    
    print(f"   → Loaded relationships for {len(job_to_skills):,} job profiles")
    print(f"   → Total job-skill relationships: {len(job_skills_df):,}")
    
    return job_skills_df, job_to_skills

def calculate_simple_job_similarity(job_a_skills: Set[str], job_b_skills: Set[str]) -> float:
    """
    Calculate simple job similarity (current approach)
    
    Returns:
        Similarity score (0-1) based on equal skill weighting
    """
    if not job_a_skills or not job_b_skills:
        return 0.0
    
    shared_skills = job_a_skills & job_b_skills
    total_skills = job_a_skills | job_b_skills
    
    return len(shared_skills) / len(total_skills) if total_skills else 0.0

def analyze_skills_gap(job_a_skills: Set[str], job_b_skills: Set[str], defining_skills: Set[str]) -> Dict[str, Any]:
    """
    Comprehensive skills gap analysis for reskilling pathway conversations
    
    Returns:
        Dict with matched/unmatched skills breakdown for both regular and defining skills
    """
    shared_skills = job_a_skills & job_b_skills
    
    # Regular skills analysis
    unmatched_a_skills = job_a_skills - job_b_skills  # Skills in A but not B
    unmatched_b_skills = job_b_skills - job_a_skills  # Skills in B but not A
    
    # Defining skills analysis
    shared_defining = []
    unmatched_a_defining = []
    unmatched_b_defining = []
    
    for skill in shared_skills:
        if skill in defining_skills:
            shared_defining.append(skill)
    
    for skill in unmatched_a_skills:
        if skill in defining_skills:
            unmatched_a_defining.append(skill)
    
    for skill in unmatched_b_skills:
        if skill in defining_skills:
            unmatched_b_defining.append(skill)
    
    return {
        'matched_skills': list(shared_skills),
        'unmatched_source_skills': list(unmatched_a_skills),
        'unmatched_target_skills': list(unmatched_b_skills),
        'matched_defining_skills': shared_defining,
        'unmatched_source_defining': unmatched_a_defining,
        'unmatched_target_defining': unmatched_b_defining,
        'skills_to_develop': len(unmatched_b_skills),        # Skills needed for target role
        'defining_skills_to_develop': len(unmatched_b_defining),  # Critical defining skills needed
        'transferable_advantage': len(shared_defining)        # Defining skills already possessed
    }

def calculate_skills_mobility_score(
    job_a_id: str,
    job_b_id: str,
    job_a_skills: Set[str], 
    job_b_skills: Set[str], 
    job_defining_skills: Dict[str, Set[str]],
    gentle_multiplier: float = 1.2
) -> Dict[str, Any]:
    """
    Calculate Skills-Based Mobility Score with gentle multiplier for job-specific defining skills
    
    This measures career transition feasibility based on shared skills, with bonus weighting
    for rare/defining skills that indicate stronger pathway viability.
    
    Args:
        job_a_id: JobProfileID for source job
        job_b_id: JobProfileID for target job
        job_a_skills: Set of skill names for job A
        job_b_skills: Set of skill names for job B
        job_defining_skills: Dict mapping JobProfileID to Set of defining skills for that job
        gentle_multiplier: Multiplier applied per shared defining skill (default 1.2 = 20% boost)
    
    Returns:
        Dict with mobility metrics and skills gap analysis
    """
    if not job_a_skills or not job_b_skills:
        return {
            'mobility_score': 0.0,
            'baseline_score': 0.0,
            'weighted_similarity': 0.0,
            'simple_similarity': 0.0,
            'shared_skills': [],
            'shared_defining_skills': [],
            'total_shared_skills': 0,
            'total_defining_shared': 0,
            'defining_skill_boost': 0.0,
            'matched_skills': [],
            'unmatched_source_skills': [],
            'unmatched_target_skills': [],
            'matched_defining_skills': [],
            'unmatched_source_defining': [],
            'unmatched_target_defining': [],
            'skills_to_develop': 0,
            'defining_skills_to_develop': 0,
            'transferable_advantage': 0
        }
    
    # Calculate simple similarity (baseline)
    shared_skills = job_a_skills & job_b_skills
    total_skills = job_a_skills | job_b_skills
    simple_similarity = len(shared_skills) / len(total_skills) if total_skills else 0.0
    
    # Get defining skills for both jobs
    job_a_defining = job_defining_skills.get(job_a_id, set())
    job_b_defining = job_defining_skills.get(job_b_id, set())
    
    # Find shared defining skills (skills that are defining for EITHER job A OR job B)
    all_defining = job_a_defining | job_b_defining
    shared_defining_skills = []
    for skill in shared_skills:
        if skill in all_defining:
            shared_defining_skills.append(skill)
    
    # Apply gentle multiplier for each shared defining skill
    defining_skill_boost = len(shared_defining_skills) * (gentle_multiplier - 1.0)
    weighted_similarity = simple_similarity * (1.0 + defining_skill_boost)
    
    # Cap at 1.0 to keep similarity meaningful
    weighted_similarity = min(1.0, weighted_similarity)
    
    # Calculate comprehensive skills gap analysis
    skills_gap_analysis = analyze_skills_gap(job_a_skills, job_b_skills, all_defining)
    
    # Convert to 0-100 scale for business interpretation
    mobility_score_100 = round(weighted_similarity * 100, 1)
    baseline_score_100 = round(simple_similarity * 100, 1)
    
    return {
        'mobility_score': mobility_score_100,           # 0-100 scale
        'baseline_score': baseline_score_100,           # 0-100 scale  
        'weighted_similarity': round(weighted_similarity, 4),  # Keep for backwards compatibility
        'simple_similarity': round(simple_similarity, 4),      # Keep for backwards compatibility
        'shared_skills': list(shared_skills),
        'shared_defining_skills': shared_defining_skills,
        'total_shared_skills': len(shared_skills),
        'total_defining_shared': len(shared_defining_skills),
        'defining_skill_boost': round(defining_skill_boost, 4),
        **skills_gap_analysis  # Include comprehensive gap analysis
    }

def create_job_specific_defining_skills(skill_universe: pd.DataFrame, job_skills_df: pd.DataFrame) -> Dict[str, Set[str]]:
    """
    Create job-specific defining skills by taking the top 25% rarest skills per job profile
    
    Args:
        skill_universe: DataFrame with all skills and their global rarity/prevalence
        job_skills_df: DataFrame with job-skill relationships
        
    Returns:
        Dict mapping JobProfileID to Set of defining skill names for that job
    """
    print("🎯 Creating job-specific defining skills (top 25% rarest per role)...")
    
    job_defining_skills = {}
    
    # Group by JobProfileID to get skills per job
    for job_id, job_group in job_skills_df.groupby('JobProfileID'):
        job_skill_names = job_group['Skill_Name'].tolist()
        
        # Get rarity info for this job's skills from skill_universe
        job_skills_with_rarity = skill_universe[skill_universe['Skill_Name'].isin(job_skill_names)].copy()
        
        # Sort by prevalence (ascending = rarest first)
        job_skills_with_rarity = job_skills_with_rarity.sort_values('prevalence_percentage')
        
        # Take top 25% rarest skills for this job
        num_defining = max(1, len(job_skills_with_rarity) // 4)  # At least 1 defining skill
        defining_for_this_job = job_skills_with_rarity.head(num_defining)['Skill_Name'].tolist()
        
        job_defining_skills[job_id] = set(defining_for_this_job)
    
    # Calculate summary statistics
    total_jobs = len(job_defining_skills)
    total_defining_relationships = sum(len(skills) for skills in job_defining_skills.values())
    avg_defining_per_job = total_defining_relationships / total_jobs if total_jobs > 0 else 0
    
    print(f"   → Created job-specific defining skills for {total_jobs:,} job profiles")
    print(f"   → Total job-skill defining relationships: {total_defining_relationships:,}")
    print(f"   → Average defining skills per job: {avg_defining_per_job:.1f}")
    
    return job_defining_skills

def analyse_job_similarity_comparison(
    job_skills_df: pd.DataFrame,
    job_to_skills: Dict[str, Set[str]],
    job_defining_skills: Dict[str, Set[str]]
) -> pd.DataFrame:
    """
    Compare baseline vs enhanced mobility scores for all job pairs

    Returns:
        DataFrame with mobility score comparisons
    """
    print(f"🔍 Analysing job mobility comparison...")

    job_ids = list(job_to_skills.keys())

        # Run full asymmetrical analysis on all directed job pairs
    print(f"🌐 Running FULL ASYMMETRICAL CORPUS analysis on {len(job_ids)} job profiles...")
    total_comparisons = len(job_ids) * (len(job_ids) - 1)  # n × (n-1) for all directed pairs
    print(f"   → Total directional comparisons: {total_comparisons:,}")
    print(f"   → This captures A→B and B→A transitions separately for complete pathway intelligence")
    
    all_pairs = []
    comparison_count = 0
    
    for job_a in job_ids:
        for job_b in job_ids:
            if job_a == job_b:  # Skip self-comparison only
                continue
            comparison_count += 1
            if comparison_count % 10000 == 0:  # Progress indicator
                print(f"   → Progress: {comparison_count:,}/{total_comparisons:,} ({comparison_count/total_comparisons*100:.1f}%)")
            
            job_a_info = job_skills_df[job_skills_df['JobProfileID'] == job_a].iloc[0]
            job_b_info = job_skills_df[job_skills_df['JobProfileID'] == job_b].iloc[0]
            
            mobility_analysis = calculate_skills_mobility_score(
                job_a,
                job_b,
                job_to_skills[job_a],
                job_to_skills[job_b],
                job_defining_skills
            )
            
            # Get comprehensive job profile details
            job_a_skills = job_to_skills[job_a]
            job_b_skills = job_to_skills[job_b]
            job_a_defining = [skill for skill in job_a_skills if skill in job_defining_skills[job_a]]
            job_b_defining = [skill for skill in job_b_skills if skill in job_defining_skills[job_b]]
            
            all_pairs.append({
                # Job Profile Identification
                'job_a_id': job_a,
                'job_a_title': job_a_info['JobProfile'],
                'job_b_id': job_b,
                'job_b_title': job_b_info['JobProfile'],
                
                # Mobility Scores (0-100 scale)
                'baseline_mobility': mobility_analysis['baseline_score'],           # 0-100 scale
                'enhanced_mobility': mobility_analysis['mobility_score'],           # 0-100 scale
                'mobility_improvement': mobility_analysis['mobility_score'] - mobility_analysis['baseline_score'],
                'defining_skill_boost': mobility_analysis['defining_skill_boost'],
                
                # Total Skills Inventory
                'job_a_total_skills': len(job_a_skills),
                'job_b_total_skills': len(job_b_skills),
                'job_a_total_defining': len(job_a_defining),
                'job_b_total_defining': len(job_b_defining),
                
                # Skills Matching Analysis
                'total_matched_skills': mobility_analysis['total_shared_skills'],
                'total_matched_defining': mobility_analysis['total_defining_shared'],
                'matched_skill_names': ', '.join(mobility_analysis['matched_skills']),
                'matched_defining_skill_names': ', '.join(mobility_analysis['matched_defining_skills']),
                
                # Skills Gap Analysis (Transition Requirements)
                'skills_needed_for_transition': mobility_analysis['skills_to_develop'],
                'defining_skills_needed': mobility_analysis['defining_skills_to_develop'],
                'needed_skill_names': ', '.join(mobility_analysis['unmatched_target_skills']),
                'needed_defining_skill_names': ', '.join(mobility_analysis['unmatched_target_defining']),
                
                # Additional Intelligence
                'skills_unique_to_source': len(mobility_analysis['unmatched_source_skills']),
                'defining_skills_unique_to_source': len(mobility_analysis['unmatched_source_defining']),
                'unique_source_skill_names': ', '.join(mobility_analysis['unmatched_source_skills']),
                'unique_source_defining_names': ', '.join(mobility_analysis['unmatched_source_defining']),
                'transferable_advantage_score': mobility_analysis['transferable_advantage'],
                
                # Transition Feasibility Metrics
                'skill_overlap_percentage': round((mobility_analysis['total_shared_skills'] / len(job_b_skills)) * 100, 1) if job_b_skills else 0,
                'defining_skill_coverage': round((mobility_analysis['total_defining_shared'] / len(job_b_defining)) * 100, 1) if job_b_defining else 0,
                'reskilling_intensity': mobility_analysis['skills_to_develop'],  # Number of skills to develop
                'critical_skill_gap': mobility_analysis['defining_skills_to_develop']  # Critical defining skills needed
            })

    comparison_df = pd.DataFrame(all_pairs)

    # Sort by mobility improvement (biggest changes first)
    comparison_df = comparison_df.sort_values('mobility_improvement', ascending=False)

    # Add quintile-based mobility scoring
    comparison_df['mobility_quintile'] = pd.qcut(
        comparison_df['enhanced_mobility'],
        q=5,
        labels=['Limited', 'Moderate', 'Good', 'Strong', 'Excellent'],
        duplicates='drop'
    )

    print(f"   → Completed {len(comparison_df):,} directional career transition analyses")
    
    # Show improvement statistics
    avg_improvement = comparison_df['mobility_improvement'].mean()
    positive_improvements = (comparison_df['mobility_improvement'] > 0).sum()
    
    print(f"   → Average defining skills mobility boost: {avg_improvement:.1f} points")
    print(f"   → Transitions with defining skills advantage: {positive_improvements}/{len(comparison_df)} ({positive_improvements/len(comparison_df)*100:.1f}%)")

    # Show comprehensive metrics summary
    print(f"   → Average skills per role: {comparison_df['job_a_total_skills'].mean():.1f}")
    print(f"   → Average defining skills per role: {comparison_df['job_a_total_defining'].mean():.1f}")
    print(f"   → Average reskilling intensity: {comparison_df['skills_needed_for_transition'].mean():.1f} skills")
    print(f"   → Average critical skill gaps: {comparison_df['defining_skills_needed'].mean():.1f} defining skills")

    return comparison_df

def generate_skill_architecture_summary(
    skill_universe: pd.DataFrame,
    defining_skills: pd.DataFrame
) -> Dict[str, Any]:
    """
    Generate comprehensive skill architecture summary
    
    Returns:
        Dict with skill architecture insights
    """
    print("🏗️ Generating skill architecture summary...")
    
    total_skills = len(skill_universe)
    
    # Rarity distribution
    rarity_dist = skill_universe['rarity_category'].value_counts()
    
    # Skill type distribution
    skill_type_dist = skill_universe['SkillType'].value_counts()
    
    # Category distribution for defining skills (unique skills only)
    if not defining_skills.empty:
        unique_defining_skills = defining_skills.drop_duplicates(subset=['Skill_ID'])
        defining_categories = unique_defining_skills['Category'].value_counts().head(10)
    else:
        defining_categories = pd.Series()
    
    # Most concentrated skills (lowest prevalence) - updated for new structure
    if not defining_skills.empty:
        most_rare = defining_skills.head(10)[['Skill_Name', 'prevalence_percentage', 'total_profiles_with_skill', 'JobProfile']]
    else:
        most_rare = pd.DataFrame()
    
    summary = {
        'total_skills': total_skills,
        'total_defining_skills': len(defining_skills),
        'defining_skill_percentage': (len(defining_skills) / total_skills) * 100,
        'rarity_distribution': rarity_dist.to_dict(),
        'skill_type_distribution': skill_type_dist.to_dict(),
        'top_defining_categories': defining_categories.to_dict(),
        'most_rare_skills': most_rare.to_dict('records')
    }
    
    return summary

# =============================================================================
# MAIN ANALYSIS FUNCTION
# =============================================================================

def analyze_skill_architecture(
    output_prefix: str = "skill_architecture",
    job_similarity_sample_size: int = 100
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Main analysis function for Skills Intelligence Engine V2
    
    Focuses on:
    1. Skill rarity intelligence (job archetype definition)
    2. Rarity-weighted job similarity (strategic foundation)
    3. Skill architecture mapping (descriptive intelligence)
    
    Returns:
        Tuple of (skill_universe, similarity_comparison, architecture_summary)
    """
    print("🎯 SKILLS INTELLIGENCE ENGINE V2 - SKILL ARCHITECTURE ANALYSIS")
    print("="*80)
    print("🏗️ Focus: Descriptive intelligence for architectural thinking")
    print("📊 Outputs: Skill rarity maps + Rarity-weighted job similarity")
    
    conn = connect_database()
    
    try:
        # Step 1: Load skill universe with rarity analysis
        print(f"\n1️⃣ SKILL RARITY INTELLIGENCE")
        print("-" * 40)
        skill_universe = load_skill_universe(conn)
        
        # Step 2: Identify defining skills with job profile context
        defining_skills = identify_defining_skills_with_context(conn, skill_universe)
        
        # Step 3: Load job-skill relationships
        print(f"\n2️⃣ JOB-SKILL RELATIONSHIP MAPPING")
        print("-" * 40)
        job_skills_df, job_to_skills = load_job_skill_matrix(conn)
        
        # Step 4: Create defining skills set for weighting
        print(f"\n3️⃣ RARITY-WEIGHTED SIMILARITY FOUNDATION")
        print("-" * 40)
        job_defining_skills = create_job_specific_defining_skills(skill_universe, job_skills_df)
        
        # Step 5: Analyse job similarity improvement
        similarity_comparison = analyse_job_similarity_comparison(
            job_skills_df, 
            job_to_skills, 
            job_defining_skills
        )
        
        # Step 6: Generate architecture summary
        print(f"\n4️⃣ SKILL ARCHITECTURE SUMMARY")
        print("-" * 40)
        architecture_summary = generate_skill_architecture_summary(skill_universe, defining_skills)
        
        # Output results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save skill universe with rarity analysis
        skill_output_path = f"{output_prefix}_skill_universe_{timestamp}.csv"
        skill_universe.to_csv(skill_output_path, index=False)
        print(f"💾 Skill universe saved: {skill_output_path}")
        
        # Save defining skills
        defining_output_path = f"{output_prefix}_defining_skills_{timestamp}.csv"
        defining_skills.to_csv(defining_output_path, index=False)
        print(f"💾 Defining skills saved: {defining_output_path}")
        
        # Save similarity comparison
        similarity_output_path = f"{output_prefix}_similarity_comparison_{timestamp}.csv"
        similarity_comparison.to_csv(similarity_output_path, index=False)
        print(f"💾 Similarity comparison saved: {similarity_output_path}")
        
        # Display key insights
        print(f"\n📊 KEY INSIGHTS")
        print("-" * 40)
        print(f"🎯 Total skills analysed: {architecture_summary['total_skills']:,}")
        print(f"🔍 Defining skills identified: {architecture_summary['total_defining_skills']:,} ({architecture_summary['defining_skill_percentage']:.1f}%)")
        
        print(f"\n📈 Rarity Distribution:")
        for category, count in architecture_summary['rarity_distribution'].items():
            percentage = (count / architecture_summary['total_skills']) * 100
            print(f"   • {category}: {count:,} skills ({percentage:.1f}%)")
        
        print(f"\n🏆 Top Categories for Defining Skills:")
        for category, count in list(architecture_summary['top_defining_categories'].items())[:5]:
            print(f"   • {category}: {count:,} defining skills")
        
        print(f"\n🔍 Most Rare Skills (with Job Profile Context):")
        for skill in architecture_summary['most_rare_skills'][:5]:
            print(f"   • {skill['Skill_Name']}: {skill['prevalence_percentage']:.2f}% ({skill['total_profiles_with_skill']} total profiles) - defines {skill['JobProfile']}")
        
        # Show similarity improvement examples
        print(f"\n🎯 Skills-Based Mobility Score Examples (Top 5 Career Transitions):")
        for _, row in similarity_comparison.head(5).iterrows():
            print(f"   • {row['job_a_title'][:30]} → {row['job_b_title'][:30]}")
            print(f"     📊 Transition Mobility: {row['baseline_mobility']:.1f} → {row['enhanced_mobility']:.1f}/100 (Defining Skills Boost: +{row['mobility_improvement']:.1f})")
            print(f"     🎯 Skills Transition: {row['job_a_total_skills']} current → {row['job_b_total_skills']} target | Already have: {row['total_matched_skills']} | Need to develop: {row['skills_needed_for_transition']}")
            print(f"     💎 Defining Skills: {row['job_a_total_defining']} current → {row['job_b_total_defining']} target | Already have: {row['total_matched_defining']} | Need to develop: {row['defining_skills_needed']}")
            if row['matched_defining_skill_names']:
                print(f"     🏆 Transferable advantages: {row['matched_defining_skill_names'][:100]}{'...' if len(row['matched_defining_skill_names']) > 100 else ''}")
            if row['needed_defining_skill_names']:
                print(f"     🎓 Critical skills to develop: {row['needed_defining_skill_names'][:100]}{'...' if len(row['needed_defining_skill_names']) > 100 else ''}")
        
        return skill_universe, similarity_comparison, architecture_summary
        
    finally:
        conn.close()
        print(f"\n🔒 Database connection closed")

# =============================================================================
# TESTING AND VALIDATION
# =============================================================================

def test_rarity_weighted_similarity():
    """Test the rarity-weighted similarity calculation with examples"""
    print("\n🧪 TESTING RARITY-WEIGHTED SIMILARITY")
    print("="*50)
    
    # Test job skills
    job_a_skills = {'Python', 'SQL', 'Machine Learning', 'Statistics'}
    job_b_skills = {'Python', 'SQL', 'Data Visualisation', 'Statistics'}
    
    # Mock job-specific defining skills (rare skills per job)
    job_defining_skills = {
        'job_a': {'Machine Learning', 'Statistics'},  # Job A's defining skills
        'job_b': {'Data Visualisation', 'Statistics'}  # Job B's defining skills
    }
    
    # Calculate mobility score
    result = calculate_skills_mobility_score('job_a', 'job_b', job_a_skills, job_b_skills, job_defining_skills)
    
    print(f"Job A skills: {job_a_skills}")
    print(f"Job B skills: {job_b_skills}")
    print(f"Shared skills: {result['shared_skills']}")
    print(f"Simple similarity: {result['simple_similarity']:.3f}")
    print(f"Weighted similarity: {result['weighted_similarity']:.3f}")
    print(f"Improvement: {result['weighted_similarity'] - result['simple_similarity']:.3f}")
    print(f"Shared defining skills: {result['shared_defining_skills']}")
    print(f"Defining skill boost: {result['defining_skill_boost']:.3f}")
    
    return result

def run_quick_validation():
    """Run quick validation of core functions"""
    print("🔍 QUICK VALIDATION OF CORE FUNCTIONS")
    print("="*50)
    
    try:
        # Test database connection
        conn = connect_database()
        conn.close()
        print("✅ Database connection: OK")
        
        # Test rarity categorisation
        test_prevalences = [2.0, 8.0, 30.0, 60.0]
        categories = [categorise_rarity(p) for p in test_prevalences]
        expected = ['Rare', 'Uncommon', 'Common', 'Universal']
        
        if categories == expected:
            print("✅ Rarity categorisation: OK")
        else:
            print(f"❌ Rarity categorisation: Expected {expected}, got {categories}")
        
        # Test similarity calculation
        test_result = test_rarity_weighted_similarity()
        if test_result['weighted_similarity'] >= test_result['simple_similarity']:
            print("✅ Rarity-weighted similarity: OK (weighted ≥ simple)")
        else:
            print("❌ Rarity-weighted similarity: Issue detected")
        
        print("\n🎉 Quick validation completed!")
        return True
        
    except Exception as e:
        print(f"❌ Validation failed: {str(e)}")
        return False

# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    print("🎯 SKILLS INTELLIGENCE ENGINE V2 - CLEAN ARCHITECTURE")
    print("="*80)
    print("🏗️ Focused on: Skill rarity intelligence + Rarity-weighted job similarity")
    print("📊 Philosophy: Descriptive intelligence for architectural thinking")
    print()
    
    # Run quick validation first
    validation_ok = run_quick_validation()
    
    if validation_ok:
        print("\n🚀 Running comprehensive skill architecture analysis...")
        
        # Run main analysis
        skill_universe, similarity_comparison, architecture_summary = analyze_skill_architecture(
            output_prefix="skills_intelligence_v2",
            job_similarity_sample_size=200  # Larger sample for better insights
        )
        
        print(f"\n🎉 ANALYSIS COMPLETE!")
        print(f"📁 Check the generated CSV files for detailed results")
        print(f"🏗️ Skills Intelligence Engine V2 is ready for strategic architecture support")
    else:
        print("\n❌ Validation failed - please check database connection and configuration") 