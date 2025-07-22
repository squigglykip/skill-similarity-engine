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
from typing import Dict, List, Tuple, Optional, Set

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
    Load complete skill universe with prevalence calculations
    
    Returns:
        DataFrame with skills, prevalence percentages, and rarity categories
    """
    print("📚 Loading skill universe...")
    
    # Get total job profiles for prevalence calculation
    total_profiles_query = "SELECT COUNT(DISTINCT JobProfileID) as total FROM jobs"
    total_profiles = pd.read_sql_query(total_profiles_query, conn).iloc[0]['total']
    
    # Calculate skill prevalence across job profiles
    skill_prevalence_query = f"""
    SELECT 
        s.Skill_ID,
        s.Skill_Name,
        s.Category,
        s.SkillType,
        COUNT(DISTINCT js.JobProfileID) as job_profiles_with_skill,
        COUNT(DISTINCT js.JobProfileID) * 100.0 / {total_profiles} as prevalence_percentage
    FROM skills s
    LEFT JOIN job_skills js ON s.Skill_ID = js.Skill_ID
    GROUP BY s.Skill_ID, s.Skill_Name, s.Category, s.SkillType
    ORDER BY prevalence_percentage ASC
    """
    
    skill_universe = pd.read_sql_query(skill_prevalence_query, conn)
    
    # Handle null values (skills not used in any job profiles)
    skill_universe['prevalence_percentage'].fillna(0.0, inplace=True)
    skill_universe['job_profiles_with_skill'].fillna(0, inplace=True)
    
    # Categorise by rarity
    skill_universe['rarity_category'] = skill_universe['prevalence_percentage'].apply(categorise_rarity)
    
    print(f"   → Loaded {len(skill_universe):,} skills")
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

def identify_defining_skills(skill_universe: pd.DataFrame, rarity_threshold: float = 5.0) -> pd.DataFrame:
    """
    Identify defining skills (rare skills that characterise specific role archetypes)
    
    Args:
        skill_universe: DataFrame with skill prevalence data
        rarity_threshold: Percentage threshold for "rare" classification
    
    Returns:
        DataFrame with defining skills and their characteristics
    """
    print(f"🎯 Identifying defining skills (prevalence < {rarity_threshold}%)...")
    
    defining_skills = skill_universe[
        skill_universe['prevalence_percentage'] < rarity_threshold
    ].copy()
    
    # Sort by rarity (least common first)
    defining_skills = defining_skills.sort_values('prevalence_percentage')
    
    print(f"   → Found {len(defining_skills):,} defining skills")
    print(f"   → Most rare: {defining_skills.iloc[0]['Skill_Name']} ({defining_skills.iloc[0]['prevalence_percentage']:.2f}%)")
    print(f"   → Least rare: {defining_skills.iloc[-1]['Skill_Name']} ({defining_skills.iloc[-1]['prevalence_percentage']:.2f}%)")
    
    return defining_skills

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
        j.JobTitle,
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

def calculate_rarity_weighted_job_similarity(
    job_a_skills: Set[str], 
    job_b_skills: Set[str], 
    skill_rarity_weights: Dict[str, float]
) -> Dict[str, any]:
    """
    Calculate rarity-weighted job similarity (enhanced approach)
    
    Args:
        job_a_skills: Set of skill names for job A
        job_b_skills: Set of skill names for job B
        skill_rarity_weights: Dict mapping skill names to rarity weights (1/prevalence)
    
    Returns:
        Dict with similarity metrics and shared rare skills analysis
    """
    if not job_a_skills or not job_b_skills:
        return {
            'weighted_similarity': 0.0,
            'simple_similarity': 0.0,
            'shared_skills': [],
            'shared_rare_skills': [],
            'total_shared_skills': 0,
            'total_rare_shared': 0
        }
    
    # Calculate simple similarity (current approach)
    shared_skills = job_a_skills & job_b_skills
    total_skills = job_a_skills | job_b_skills
    simple_similarity = len(shared_skills) / len(total_skills) if total_skills else 0.0
    
    # Calculate weighted similarity (enhanced approach)
    # Weight by inverse rarity (rare skills matter more)
    weighted_overlap = 0.0
    max_possible_weight = 0.0
    
    # Calculate weighted overlap for shared skills
    for skill in shared_skills:
        weight = skill_rarity_weights.get(skill, 1.0)  # Default weight if skill not found
        weighted_overlap += weight
    
    # Calculate maximum possible weight
    for skill in total_skills:
        weight = skill_rarity_weights.get(skill, 1.0)
        max_possible_weight += weight
    
    weighted_similarity = weighted_overlap / max_possible_weight if max_possible_weight > 0 else 0.0
    
    # Analyse shared skills by rarity
    shared_rare_skills = []
    for skill in shared_skills:
        # Consider skills with weight > 5 as "rare" (prevalence < 20%)
        if skill_rarity_weights.get(skill, 1.0) > 5:
            shared_rare_skills.append(skill)
    
    return {
        'weighted_similarity': round(weighted_similarity, 4),
        'simple_similarity': round(simple_similarity, 4),
        'shared_skills': list(shared_skills),
        'shared_rare_skills': shared_rare_skills,
        'total_shared_skills': len(shared_skills),
        'total_rare_shared': len(shared_rare_skills)
    }

def create_skill_rarity_weights(skill_universe: pd.DataFrame) -> Dict[str, float]:
    """
    Create rarity weights for skills (inverse of prevalence)
    
    Returns:
        Dict mapping skill names to rarity weights
    """
    print("⚖️ Creating skill rarity weights...")
    
    skill_weights = {}
    
    for _, skill in skill_universe.iterrows():
        skill_name = skill['Skill_Name']
        prevalence = skill['prevalence_percentage']
        
        # Weight = 1 / (prevalence/100), with minimum prevalence of 0.1% to avoid extreme weights
        adjusted_prevalence = max(prevalence, 0.1) / 100
        weight = 1.0 / adjusted_prevalence
        
        skill_weights[skill_name] = weight
    
    # Show weight distribution
    weights_array = np.array(list(skill_weights.values()))
    print(f"   → Created weights for {len(skill_weights):,} skills")
    print(f"   → Weight range: {weights_array.min():.1f} - {weights_array.max():.1f}")
    print(f"   → Median weight: {np.median(weights_array):.1f}")
    
    return skill_weights

def analyse_job_similarity_comparison(
    job_skills_df: pd.DataFrame,
    job_to_skills: Dict[str, Set[str]],
    skill_rarity_weights: Dict[str, float],
    sample_size: int = 100
) -> pd.DataFrame:
    """
    Compare simple vs rarity-weighted similarity for sample job pairs
    
    Returns:
        DataFrame with similarity comparisons
    """
    print(f"🔍 Analysing job similarity comparison (sample size: {sample_size})...")
    
    job_ids = list(job_to_skills.keys())
    
    # Sample random job pairs
    np.random.seed(42)  # For reproducible results
    sample_pairs = []
    
    for _ in range(sample_size):
        job_a, job_b = np.random.choice(job_ids, 2, replace=False)
        
        job_a_info = job_skills_df[job_skills_df['JobProfileID'] == job_a].iloc[0]
        job_b_info = job_skills_df[job_skills_df['JobProfileID'] == job_b].iloc[0]
        
        similarity_analysis = calculate_rarity_weighted_job_similarity(
            job_to_skills[job_a],
            job_to_skills[job_b],
            skill_rarity_weights
        )
        
        sample_pairs.append({
            'job_a_id': job_a,
            'job_a_title': job_a_info['JobTitle'],
            'job_b_id': job_b,
            'job_b_title': job_b_info['JobTitle'],
            'simple_similarity': similarity_analysis['simple_similarity'],
            'weighted_similarity': similarity_analysis['weighted_similarity'],
            'similarity_improvement': similarity_analysis['weighted_similarity'] - similarity_analysis['simple_similarity'],
            'total_shared_skills': similarity_analysis['total_shared_skills'],
            'rare_shared_skills': similarity_analysis['total_rare_shared'],
            'shared_rare_skill_names': ', '.join(similarity_analysis['shared_rare_skills'][:3])  # Top 3 for display
        })
    
    comparison_df = pd.DataFrame(sample_pairs)
    
    # Sort by similarity improvement (biggest changes first)
    comparison_df = comparison_df.sort_values('similarity_improvement', ascending=False)
    
    print(f"   → Completed {len(comparison_df):,} job pair comparisons")
    
    # Show improvement statistics
    avg_improvement = comparison_df['similarity_improvement'].mean()
    positive_improvements = (comparison_df['similarity_improvement'] > 0).sum()
    
    print(f"   → Average similarity improvement: {avg_improvement:.4f}")
    print(f"   → Pairs with positive improvement: {positive_improvements}/{len(comparison_df)} ({positive_improvements/len(comparison_df)*100:.1f}%)")
    
    return comparison_df

def generate_skill_architecture_summary(
    skill_universe: pd.DataFrame,
    defining_skills: pd.DataFrame
) -> Dict[str, any]:
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
    
    # Category distribution for defining skills
    defining_categories = defining_skills['Category'].value_counts().head(10)
    
    # Most concentrated skills (lowest prevalence)
    most_rare = defining_skills.head(10)[['Skill_Name', 'prevalence_percentage', 'job_profiles_with_skill']]
    
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
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, any]]:
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
        
        # Step 2: Identify defining skills
        defining_skills = identify_defining_skills(skill_universe)
        
        # Step 3: Load job-skill relationships
        print(f"\n2️⃣ JOB-SKILL RELATIONSHIP MAPPING")
        print("-" * 40)
        job_skills_df, job_to_skills = load_job_skill_matrix(conn)
        
        # Step 4: Create rarity weights
        print(f"\n3️⃣ RARITY-WEIGHTED SIMILARITY FOUNDATION")
        print("-" * 40)
        skill_rarity_weights = create_skill_rarity_weights(skill_universe)
        
        # Step 5: Analyse job similarity improvement
        similarity_comparison = analyse_job_similarity_comparison(
            job_skills_df, 
            job_to_skills, 
            skill_rarity_weights,
            sample_size=job_similarity_sample_size
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
        
        print(f"\n🔍 Most Rare Skills:")
        for skill in architecture_summary['most_rare_skills'][:5]:
            print(f"   • {skill['Skill_Name']}: {skill['prevalence_percentage']:.2f}% ({skill['job_profiles_with_skill']} job profiles)")
        
        # Show similarity improvement examples
        print(f"\n⚖️ Rarity-Weighted Similarity Examples (Top 5 Improvements):")
        for _, row in similarity_comparison.head(5).iterrows():
            print(f"   • {row['job_a_title'][:25]} ↔ {row['job_b_title'][:25]}")
            print(f"     Simple: {row['simple_similarity']:.3f} → Weighted: {row['weighted_similarity']:.3f} (Δ+{row['similarity_improvement']:.3f})")
            if row['shared_rare_skill_names']:
                print(f"     Rare skills: {row['shared_rare_skill_names']}")
        
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
    
    # Create test data
    job_a_skills = {'Python', 'SQL', 'Machine Learning', 'Statistics'}
    job_b_skills = {'Python', 'SQL', 'Data Visualisation', 'Statistics'}
    
    # Mock rarity weights (higher weight = rarer skill)
    skill_weights = {
        'Python': 2.0,          # Common skill (50% prevalence)
        'SQL': 2.5,             # Common skill (40% prevalence)
        'Machine Learning': 10.0, # Rare skill (10% prevalence)
        'Statistics': 5.0,       # Uncommon skill (20% prevalence)
        'Data Visualisation': 4.0 # Uncommon skill (25% prevalence)
    }
    
    # Calculate similarities
    result = calculate_rarity_weighted_job_similarity(job_a_skills, job_b_skills, skill_weights)
    
    print(f"Job A skills: {job_a_skills}")
    print(f"Job B skills: {job_b_skills}")
    print(f"Shared skills: {result['shared_skills']}")
    print(f"Simple similarity: {result['simple_similarity']:.3f}")
    print(f"Weighted similarity: {result['weighted_similarity']:.3f}")
    print(f"Improvement: {result['weighted_similarity'] - result['simple_similarity']:.3f}")
    print(f"Shared rare skills: {result['shared_rare_skills']}")
    
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