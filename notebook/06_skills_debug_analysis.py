#!/usr/bin/env python3
"""
Skills Intelligence Debug Analysis
==================================

Debug script to investigate issues with gateway skills detection, skill rarity distributions,
and scoring patterns in the skills intelligence engine.

Key Debug Areas:
1. Gateway skills detection logic and criteria
2. Skill rarity distribution across job profiles and functions
3. Perfect score patterns (why many pairs score exactly 64.5%)
4. Cross-functional transition patterns
5. Defining skills selection and weighting
"""

import pandas as pd
import numpy as np
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict, Counter
import warnings

warnings.filterwarnings('ignore')

# =============================================================================
# CONFIGURATION
# =============================================================================

DATABASE_FILE = "models/2025-Q3/workforce_intelligence.sqlite"

# Same thresholds as main analysis for consistency
SKILL_RARITY_THRESHOLDS = {
    'rare': 5.0,        # <5% = rare skill
    'uncommon': 20.0,   # 5-20% = uncommon skill  
    'common': 50.0,     # 20-50% = common skill
}

GATEWAY_SKILLS_CONFIG = {
    'min_cross_function_jobs': 3,      # Minimum jobs across functions to be gateway
    'gateway_prevalence_threshold': 15, # Skills in 15-40% of roles can be gateways
    'max_gateway_prevalence': 40       # Too universal to be a gateway
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
# DEBUG FUNCTIONS
# =============================================================================

def debug_database_structure(conn):
    """Examine the database structure and data quality"""
    print_section_header("DATABASE STRUCTURE DEBUG")
    
    # Check table sizes
    tables = ['jobs', 'job_skills', 'skills']
    for table in tables:
        count = pd.read_sql_query(f"SELECT COUNT(*) as count FROM {table}", conn).iloc[0]['count']
        print(f"📊 {table}: {count:,} records")
    
    # Check job function distribution
    job_functions = pd.read_sql_query("""
        SELECT JobFunction, COUNT(*) as job_count 
        FROM jobs 
        WHERE JobFunction IS NOT NULL 
        GROUP BY JobFunction 
        ORDER BY job_count DESC
    """, conn)
    
    print(f"\n🏢 Job Function Distribution:")
    for _, row in job_functions.head(10).iterrows():
        print(f"   → {row['JobFunction']}: {row['job_count']} jobs")
    
    print(f"   → Total job functions: {len(job_functions)}")
    
    # Check skills distribution basics
    skills_info = pd.read_sql_query("""
        SELECT 
            COUNT(DISTINCT Skill_ID) as unique_skills,
            COUNT(DISTINCT JobProfileID) as jobs_with_skills,
            COUNT(*) as total_relationships,
            AVG(Skill_Weight) as avg_weight
        FROM job_skills
    """, conn)
    
    print(f"\n📚 Skills Overview:")
    for col, val in skills_info.iloc[0].items():
        if col == 'avg_weight':
            print(f"   → {col}: {val:.3f}")
        else:
            print(f"   → {col}: {val:,}")

def debug_skill_prevalence_calculation(conn):
    """Debug skill prevalence and rarity calculations"""
    print_section_header("SKILL PREVALENCE DEBUG")
    
    # Load data
    job_skills_df = pd.read_sql_query("SELECT * FROM job_skills", conn)
    jobs_df = pd.read_sql_query("SELECT JobProfileID FROM jobs", conn)
    total_jobs = len(jobs_df)
    
    print(f"📊 Total jobs for prevalence calculation: {total_jobs:,}")
    
    # Calculate prevalence
    skill_prevalence = job_skills_df.groupby('Skill_ID').agg({
        'JobProfileID': 'nunique'
    }).reset_index()
    
    skill_prevalence['prevalence_count'] = skill_prevalence['JobProfileID']
    skill_prevalence['prevalence_percentage'] = (skill_prevalence['prevalence_count'] / total_jobs) * 100
    skill_prevalence['rarity_category'] = skill_prevalence['prevalence_percentage'].apply(categorize_skill_rarity)
    
    # Analyze distribution
    print(f"📈 Skill Prevalence Distribution:")
    prevalence_stats = skill_prevalence['prevalence_percentage'].describe()
    for stat, value in prevalence_stats.items():
        print(f"   → {stat}: {value:.2f}%")
    
    # Rarity category distribution
    print(f"\n🔍 Rarity Category Distribution:")
    rarity_dist = skill_prevalence['rarity_category'].value_counts()
    for category, count in rarity_dist.items():
        percentage = (count / len(skill_prevalence)) * 100
        avg_prevalence = skill_prevalence[skill_prevalence['rarity_category'] == category]['prevalence_percentage'].mean()
        print(f"   → {category.capitalize()}: {count:,} skills ({percentage:.1f}% of all skills, avg prevalence: {avg_prevalence:.2f}%)")
    
    # Show examples of each rarity category
    print(f"\n📋 Examples by Rarity Category:")
    for category in ['rare', 'uncommon', 'common', 'universal']:
        category_skills = skill_prevalence[skill_prevalence['rarity_category'] == category]
        if len(category_skills) > 0:
            print(f"\n   {category.upper()} Skills (top 5):")
            for _, skill in category_skills.nlargest(5, 'prevalence_percentage').iterrows():
                print(f"      → Skill {skill['Skill_ID']}: {skill['prevalence_percentage']:.2f}% ({skill['prevalence_count']} jobs)")
    
    return skill_prevalence

def debug_gateway_skills_detection(conn, skill_prevalence):
    """Debug why gateway skills detection is returning 0 results"""
    print_section_header("GATEWAY SKILLS DETECTION DEBUG")
    
    # Load data
    job_skills_df = pd.read_sql_query("SELECT * FROM job_skills", conn)
    jobs_df = pd.read_sql_query("SELECT JobProfileID, JobFunction FROM jobs WHERE JobFunction IS NOT NULL", conn)
    
    print(f"📊 Jobs with functions: {len(jobs_df):,}")
    print(f"📊 Unique job functions: {jobs_df['JobFunction'].nunique()}")
    
    # Merge job skills with job function information
    job_skills_with_function = job_skills_df.merge(jobs_df, on='JobProfileID', how='inner')
    
    print(f"📊 Job-skills records with function info: {len(job_skills_with_function):,}")
    
    # Calculate skill distribution across job functions
    skill_function_dist = job_skills_with_function.groupby('Skill_ID').agg({
        'JobFunction': 'nunique',
        'JobProfileID': 'nunique'
    }).reset_index()
    
    skill_function_dist = skill_function_dist.rename(columns={
        'JobFunction': 'num_functions',
        'JobProfileID': 'num_jobs'
    })
    
    # Merge with prevalence data
    skill_function_dist = skill_function_dist.merge(
        skill_prevalence[['Skill_ID', 'prevalence_percentage']], 
        on='Skill_ID', 
        how='left'
    )
    
    print(f"\n🔍 Function Distribution Analysis:")
    function_dist = skill_function_dist['num_functions'].value_counts().sort_index()
    for num_funcs, count in function_dist.items():
        percentage = (count / len(skill_function_dist)) * 100
        print(f"   → Skills in {num_funcs} function(s): {count:,} skills ({percentage:.1f}%)")
    
    # Debug gateway criteria step by step
    print(f"\n🔬 Gateway Skills Criteria Analysis:")
    print(f"   Criteria 1 - Min functions: ≥{GATEWAY_SKILLS_CONFIG['min_cross_function_jobs']}")
    criteria1 = skill_function_dist['num_functions'] >= GATEWAY_SKILLS_CONFIG['min_cross_function_jobs']
    print(f"   → Meets criteria 1: {criteria1.sum():,} skills")
    
    print(f"   Criteria 2 - Min prevalence: ≥{GATEWAY_SKILLS_CONFIG['gateway_prevalence_threshold']}%")
    criteria2 = skill_function_dist['prevalence_percentage'] >= GATEWAY_SKILLS_CONFIG['gateway_prevalence_threshold']
    print(f"   → Meets criteria 2: {criteria2.sum():,} skills")
    
    print(f"   Criteria 3 - Max prevalence: ≤{GATEWAY_SKILLS_CONFIG['max_gateway_prevalence']}%")
    criteria3 = skill_function_dist['prevalence_percentage'] <= GATEWAY_SKILLS_CONFIG['max_gateway_prevalence']
    print(f"   → Meets criteria 3: {criteria3.sum():,} skills")
    
    # Combined criteria
    all_criteria = criteria1 & criteria2 & criteria3
    print(f"   → Meets ALL criteria: {all_criteria.sum():,} skills")
    
    # Show skills that almost meet criteria
    print(f"\n📋 Skills Close to Gateway Criteria:")
    
    # Skills with good function coverage but wrong prevalence
    good_coverage = skill_function_dist[criteria1]
    if len(good_coverage) > 0:
        print(f"\n   Skills with ≥{GATEWAY_SKILLS_CONFIG['min_cross_function_jobs']} functions:")
        for _, skill in good_coverage.nlargest(10, 'num_functions').iterrows():
            status = "✅" if (skill['prevalence_percentage'] >= GATEWAY_SKILLS_CONFIG['gateway_prevalence_threshold'] and 
                           skill['prevalence_percentage'] <= GATEWAY_SKILLS_CONFIG['max_gateway_prevalence']) else "❌"
            print(f"      → {status} Skill {skill['Skill_ID']}: {skill['num_functions']} functions, {skill['prevalence_percentage']:.2f}% prevalence")
    
    # Adjust criteria for debugging if no gateway skills found
    if all_criteria.sum() == 0:
        print(f"\n🔧 ADJUSTED CRITERIA DEBUG (more lenient):")
        adjusted_criteria = (
            (skill_function_dist['num_functions'] >= 2) &  # Reduce from 3 to 2
            (skill_function_dist['prevalence_percentage'] >= 10) &  # Reduce from 15 to 10
            (skill_function_dist['prevalence_percentage'] <= 50)    # Increase from 40 to 50
        )
        print(f"   → With adjusted criteria: {adjusted_criteria.sum():,} skills")
        
        if adjusted_criteria.sum() > 0:
            print(f"   Top candidates with adjusted criteria:")
            candidates = skill_function_dist[adjusted_criteria].nlargest(10, 'num_functions')
            for _, skill in candidates.iterrows():
                print(f"      → Skill {skill['Skill_ID']}: {skill['num_functions']} functions, {skill['prevalence_percentage']:.2f}% prevalence")

def debug_defining_skills_selection(conn):
    """Debug defining skills selection logic"""
    print_section_header("DEFINING SKILLS SELECTION DEBUG")
    
    # Load data
    job_skills_df = pd.read_sql_query("SELECT * FROM job_skills", conn)
    jobs_df = pd.read_sql_query("SELECT JobProfileID, JobProfile FROM jobs", conn)
    
    # Sample a few jobs for detailed analysis
    sample_jobs = jobs_df.sample(5, random_state=42)
    
    print(f"🔍 Analyzing defining skills for sample jobs:")
    
    for _, job in sample_jobs.iterrows():
        job_id = job['JobProfileID']
        job_name = job['JobProfile']
        
        # Get skills for this job
        job_skills = job_skills_df[job_skills_df['JobProfileID'] == job_id]
        
        print(f"\n📋 Job: {job_name} ({job_id})")
        print(f"   → Total skills: {len(job_skills)}")
        
        if len(job_skills) > 0:
            print(f"   → Top skills by weight:")
            top_skills = job_skills.nlargest(5, 'Skill_Weight')
            for _, skill in top_skills.iterrows():
                print(f"      → Skill {skill['Skill_ID']}: weight {skill['Skill_Weight']:.3f}")
            
            # Calculate basic defining score (without rarity info for now)
            print(f"   → Skill weight distribution:")
            print(f"      → Mean: {job_skills['Skill_Weight'].mean():.3f}")
            print(f"      → Max: {job_skills['Skill_Weight'].max():.3f}")
            print(f"      → Min: {job_skills['Skill_Weight'].min():.3f}")

def debug_perfect_scores_pattern(conn):
    """Debug why many pairs score exactly 64.5%"""
    print_section_header("PERFECT SCORES PATTERN DEBUG")
    
    # This would require running the main analysis, but we can examine the scoring formula
    print("🧮 Skills Confidence Scoring Formula:")
    weights = {
        'defining_skills_overlap': 0.40,
        'total_skills_coverage': 0.20,
        'rarity_bonus': 0.15,
        'gateway_skills_bonus': 0.10,
        'skill_gap_penalty': 0.15
    }
    
    print("   Component weights:")
    for component, weight in weights.items():
        print(f"      → {component}: {weight:.2f} ({weight*100:.0f}%)")
    
    # Calculate what combination gives 64.5%
    target_score = 64.5
    
    print(f"\n🎯 To achieve {target_score}% score:")
    print("   Example combinations:")
    
    # Perfect defining + coverage, no gateway, no gaps
    defining = 1.0 * weights['defining_skills_overlap'] * 100  # 40%
    coverage = 1.0 * weights['total_skills_coverage'] * 100    # 20%
    rarity = 0.3 * weights['rarity_bonus'] * 100               # 4.5%
    gateway = 0.0 * weights['gateway_skills_bonus'] * 100      # 0%
    gap_penalty = 0.0 * weights['skill_gap_penalty'] * 100     # 0%
    
    total = defining + coverage + rarity + gateway - gap_penalty
    
    print(f"      → Perfect overlap (100%) + Perfect coverage (100%) + 30% rarity bonus = {total:.1f}%")
    print("      → This suggests many job pairs have:")
    print("         • Perfect defining skills overlap")
    print("         • Perfect total skills coverage") 
    print("         • Consistent rarity bonus (~30%)")
    print("         • No gateway skills")
    print("         • No skill gaps")

def debug_cross_functional_patterns(conn):
    """Debug cross-functional transition patterns"""
    print_section_header("CROSS-FUNCTIONAL PATTERNS DEBUG")
    
    # Load jobs data
    jobs_df = pd.read_sql_query("SELECT JobProfileID, JobProfile, JobFunction FROM jobs WHERE JobFunction IS NOT NULL", conn)
    
    print(f"📊 Jobs with function data: {len(jobs_df):,}")
    
    # Function distribution
    function_dist = jobs_df['JobFunction'].value_counts()
    print(f"📊 Job function distribution:")
    for func, count in function_dist.head(10).items():
        percentage = (count / len(jobs_df)) * 100
        print(f"   → {func}: {count} jobs ({percentage:.1f}%)")
    
    # Calculate potential cross-functional pairs
    total_jobs = len(jobs_df)
    same_function_pairs = sum(count * count for count in function_dist.values)
    cross_function_pairs = (total_jobs * total_jobs) - same_function_pairs
    
    print(f"\n🔄 Transition Potential:")
    print(f"   → Total possible pairs: {total_jobs * total_jobs:,}")
    print(f"   → Same function pairs: {same_function_pairs:,} ({same_function_pairs/(total_jobs*total_jobs)*100:.1f}%)")
    print(f"   → Cross-functional pairs: {cross_function_pairs:,} ({cross_function_pairs/(total_jobs*total_jobs)*100:.1f}%)")

# =============================================================================
# MAIN DEBUG EXECUTION
# =============================================================================

def main():
    """Run comprehensive debug analysis"""
    print_section_header(
        "SKILLS INTELLIGENCE DEBUG ANALYSIS",
        "Comprehensive debugging of gateway skills, rarity patterns, and scoring logic"
    )
    
    # Connect to database
    print(f"🔗 Connecting to database: {DATABASE_FILE}")
    conn = sqlite3.connect(DATABASE_FILE)
    
    try:
        # Run debug analyses
        debug_database_structure(conn)
        skill_prevalence = debug_skill_prevalence_calculation(conn)
        debug_gateway_skills_detection(conn, skill_prevalence)
        debug_defining_skills_selection(conn)
        debug_perfect_scores_pattern(conn)
        debug_cross_functional_patterns(conn)
        
        print_section_header("DEBUG SUMMARY & RECOMMENDATIONS")
        print("🔍 Key findings will help explain:")
        print("   → Why gateway skills detection returned 0 results")
        print("   → Whether skill rarity distribution is realistic")
        print("   → Why many pairs score exactly 64.5%")
        print("   → How cross-functional patterns emerge")
        
        print("\n💡 Next steps based on findings:")
        print("   → Adjust gateway criteria if too restrictive")
        print("   → Validate scoring formula logic")
        print("   → Consider real vs synthetic data limitations")
        
    finally:
        conn.close()
        print(f"\n🔒 Database connection closed")

if __name__ == "__main__":
    main() 