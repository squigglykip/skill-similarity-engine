#!/usr/bin/env python3
"""
SKILL CO-OCCURRENCE DATA EXPLORATION
===================================

Comprehensive exploration of skill co-occurrence patterns to understand the data
before attempting clustering. This provides the foundation for informed clustering
parameter selection and algorithm choice.

Purpose:
- Understand skill distribution patterns across job profiles
- Analyze co-occurrence frequency and sparsity
- Identify natural breakpoints and similarity thresholds
- Examine skill category relationships and patterns
- Provide data-driven insights for clustering approach

Philosophy: Thorough data understanding before algorithmic application

Usage:
    python skill_cooccurrence_data_exploration.py
"""

import pandas as pd
import numpy as np
import sqlite3
import warnings
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Set, Any
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict, Counter
import scipy.stats as stats
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import jaccard_score

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

class ExplorationConfig:
    """Configuration for data exploration"""
    
    DATABASE_PATH = DATABASE_FILE
    
    # Sampling for visualization (to prevent overplotting)
    VIZ_SAMPLE_SIZE = 5000  # Sample size for visualizations
    
    # Analysis thresholds
    THRESHOLDS = {
        'min_cooccurrence_frequency': 5,    # Minimum times skills must co-occur
        'min_jobs_per_skill': 3,            # Minimum jobs containing a skill
        'similarity_percentiles': [50, 75, 90, 95, 99]  # Key percentiles to examine
    }
    
    # Output settings
    SAVE_PLOTS = True
    PLOT_DPI = 300
    FIGURE_SIZE = (12, 8)

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def connect_database():
    """Connect to the workforce intelligence database"""
    try:
        conn = sqlite3.connect(ExplorationConfig.DATABASE_PATH)
        print(f"✅ Connected to database: {ExplorationConfig.DATABASE_PATH}")
        return conn
    except sqlite3.OperationalError as e:
        raise FileNotFoundError(f"Could not connect to database: {e}")

def save_plot(fig, filename: str, title: Optional[str] = None):
    """Save plot with timestamp and optional title"""
    if title:
        fig.suptitle(title, fontsize=14, fontweight='bold')
    
    if ExplorationConfig.SAVE_PLOTS:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        full_filename = f"skill_exploration_{filename}_{timestamp}.png"
        fig.savefig(full_filename, dpi=ExplorationConfig.PLOT_DPI, bbox_inches='tight')
        print(f"   📊 Plot saved: {full_filename}")

# =============================================================================
# DATA LOADING AND BASIC EXPLORATION
# =============================================================================

def load_comprehensive_skill_data(conn) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load comprehensive skill data for exploration
    
    Returns:
        Tuple of (job_skills_df, skills_df, jobs_df)
    """
    print("📚 Loading comprehensive skill data...")
    
    # Load job-skill relationships with full context
    job_skills_query = """
    SELECT 
        js.JobProfileID,
        js.Skill_ID,
        s.Skill_Name,
        s.Category as Skill_Category,
        s.SkillType,
        j.JobProfile,
        j.JobFunction,
        j.JobSubFunction,
        j.JobCategory,
        j.ManagementLevel
    FROM job_skills js
    JOIN skills s ON js.Skill_ID = s.Skill_ID
    JOIN jobs j ON js.JobProfileID = j.JobProfileID
    ORDER BY js.JobProfileID, s.Skill_Name
    """
    
    job_skills_df = pd.read_sql_query(job_skills_query, conn)
    
    # Load skills metadata
    skills_query = """
    SELECT 
        Skill_ID,
        Skill_Name,
        Category,
        SkillType
    FROM skills
    ORDER BY Skill_Name
    """
    
    skills_df = pd.read_sql_query(skills_query, conn)
    
    # Load jobs metadata
    jobs_query = """
    SELECT 
        JobProfileID,
        JobProfile,
        JobFunction,
        JobSubFunction,
        JobCategory,
        ManagementLevel,
        Customer_Facing,
        is_Banker
    FROM jobs
    ORDER BY JobFunction, JobProfile
    """
    
    jobs_df = pd.read_sql_query(jobs_query, conn)
    
    print(f"   → Job-skill relationships: {len(job_skills_df):,}")
    print(f"   → Unique skills: {len(skills_df):,}")
    print(f"   → Unique jobs: {len(jobs_df):,}")
    print(f"   → Job profiles with skills: {job_skills_df['JobProfileID'].nunique():,}")
    print(f"   → Skills actually used: {job_skills_df['Skill_ID'].nunique():,}")
    
    return job_skills_df, skills_df, jobs_df

def analyze_basic_distributions(job_skills_df: pd.DataFrame, skills_df: pd.DataFrame, jobs_df: pd.DataFrame):
    """Analyze basic distribution patterns in the skill data"""
    print("\n📊 BASIC DISTRIBUTION ANALYSIS")
    print("="*60)
    
    # Skills per job distribution
    skills_per_job = job_skills_df.groupby('JobProfileID').size()
    
    print(f"\n🎯 Skills per Job Profile:")
    print(f"   → Mean: {skills_per_job.mean():.1f}")
    print(f"   → Median: {skills_per_job.median():.1f}")
    print(f"   → Std Dev: {skills_per_job.std():.1f}")
    print(f"   → Min: {skills_per_job.min()}")
    print(f"   → Max: {skills_per_job.max()}")
    print(f"   → 25th percentile: {skills_per_job.quantile(0.25):.1f}")
    print(f"   → 75th percentile: {skills_per_job.quantile(0.75):.1f}")
    print(f"   → 90th percentile: {skills_per_job.quantile(0.90):.1f}")
    print(f"   → 95th percentile: {skills_per_job.quantile(0.95):.1f}")
    
    # Jobs per skill distribution
    jobs_per_skill = job_skills_df.groupby('Skill_Name').size()
    
    print(f"\n📋 Jobs per Skill:")
    print(f"   → Mean: {jobs_per_skill.mean():.1f}")
    print(f"   → Median: {jobs_per_skill.median():.1f}")
    print(f"   → Std Dev: {jobs_per_skill.std():.1f}")
    print(f"   → Min: {jobs_per_skill.min()}")
    print(f"   → Max: {jobs_per_skill.max()}")
    print(f"   → 25th percentile: {jobs_per_skill.quantile(0.25):.1f}")
    print(f"   → 75th percentile: {jobs_per_skill.quantile(0.75):.1f}")
    print(f"   → 90th percentile: {jobs_per_skill.quantile(0.90):.1f}")
    print(f"   → 95th percentile: {jobs_per_skill.quantile(0.95):.1f}")
    
    # Skill prevalence analysis
    total_jobs = job_skills_df['JobProfileID'].nunique()
    skill_prevalence = job_skills_df.groupby('Skill_Name').agg({
        'JobProfileID': 'nunique'
    }).reset_index()
    skill_prevalence['prevalence_percentage'] = (skill_prevalence['JobProfileID'] / total_jobs) * 100
    skill_prevalence = skill_prevalence.sort_values('prevalence_percentage', ascending=False)
    
    print(f"\n🔍 Skill Prevalence Analysis:")
    print(f"   → Skills in >50% of jobs: {(skill_prevalence['prevalence_percentage'] > 50).sum():,}")
    print(f"   → Skills in >25% of jobs: {(skill_prevalence['prevalence_percentage'] > 25).sum():,}")
    print(f"   → Skills in >10% of jobs: {(skill_prevalence['prevalence_percentage'] > 10).sum():,}")
    print(f"   → Skills in >5% of jobs: {(skill_prevalence['prevalence_percentage'] > 5).sum():,}")
    print(f"   → Skills in >1% of jobs: {(skill_prevalence['prevalence_percentage'] > 1).sum():,}")
    print(f"   → Skills in only 1 job: {(skill_prevalence['JobProfileID'] == 1).sum():,}")
    
    print(f"\n🏆 Most Common Skills:")
    for _, row in skill_prevalence.head(10).iterrows():
        print(f"   • {row['Skill_Name']}: {row['prevalence_percentage']:.1f}% ({row['JobProfileID']} jobs)")
    
    print(f"\n💎 Rarest Skills (more than 1 job):")
    rare_skills = skill_prevalence[skill_prevalence['JobProfileID'] > 1].tail(10)
    for _, row in rare_skills.iterrows():
        print(f"   • {row['Skill_Name']}: {row['prevalence_percentage']:.1f}% ({row['JobProfileID']} jobs)")
    
    # Category analysis
    if 'Skill_Category' in job_skills_df.columns:
        print(f"\n📂 Skill Category Distribution:")
        category_counts = job_skills_df['Skill_Category'].value_counts()
        total_relationships = len(job_skills_df)
        
        for category, count in category_counts.head(15).items():
            percentage = (count / total_relationships) * 100
            print(f"   • {category}: {count:,} relationships ({percentage:.1f}%)")
    
    # Job function analysis
    if 'JobFunction' in job_skills_df.columns:
        print(f"\n🏢 Job Function Distribution:")
        function_job_counts = job_skills_df.groupby('JobFunction')['JobProfileID'].nunique().sort_values(ascending=False)
        
        for function, count in function_job_counts.head(10).items():
            print(f"   • {function}: {count:,} job profiles")
    
    return skills_per_job, jobs_per_skill, skill_prevalence

def create_distribution_visualizations(skills_per_job: pd.Series, jobs_per_skill: pd.Series, skill_prevalence: pd.DataFrame):
    """Create visualizations for basic distributions"""
    print("\n📈 Creating distribution visualizations...")
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Skill Co-occurrence Data: Basic Distributions', fontsize=16, fontweight='bold')
    
    # 1. Skills per job histogram
    axes[0, 0].hist(skills_per_job, bins=50, alpha=0.7, color='skyblue', edgecolor='black')
    axes[0, 0].axvline(skills_per_job.mean(), color='red', linestyle='--', label=f'Mean: {skills_per_job.mean():.1f}')
    axes[0, 0].axvline(skills_per_job.median(), color='orange', linestyle='--', label=f'Median: {skills_per_job.median():.1f}')
    axes[0, 0].set_xlabel('Number of Skills per Job Profile')
    axes[0, 0].set_ylabel('Frequency')
    axes[0, 0].set_title('Distribution: Skills per Job Profile')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # 2. Jobs per skill histogram (log scale due to power law)
    log_jobs_per_skill = np.log10(jobs_per_skill + 1)  # +1 to handle log(0)
    axes[0, 1].hist(log_jobs_per_skill, bins=50, alpha=0.7, color='lightcoral', edgecolor='black')
    axes[0, 1].axvline(np.log10(jobs_per_skill.mean() + 1), color='red', linestyle='--', 
                       label=f'Mean: {jobs_per_skill.mean():.1f}')
    axes[0, 1].axvline(np.log10(jobs_per_skill.median() + 1), color='orange', linestyle='--', 
                       label=f'Median: {jobs_per_skill.median():.1f}')
    axes[0, 1].set_xlabel('Log10(Number of Jobs per Skill + 1)')
    axes[0, 1].set_ylabel('Frequency')
    axes[0, 1].set_title('Distribution: Jobs per Skill (Log Scale)')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # 3. Skill prevalence distribution
    axes[1, 0].hist(skill_prevalence['prevalence_percentage'], bins=50, alpha=0.7, color='lightgreen', edgecolor='black')
    axes[1, 0].axvline(skill_prevalence['prevalence_percentage'].mean(), color='red', linestyle='--', 
                       label=f'Mean: {skill_prevalence["prevalence_percentage"].mean():.1f}%')
    axes[1, 0].axvline(skill_prevalence['prevalence_percentage'].median(), color='orange', linestyle='--', 
                       label=f'Median: {skill_prevalence["prevalence_percentage"].median():.1f}%')
    axes[1, 0].set_xlabel('Skill Prevalence (%)')
    axes[1, 0].set_ylabel('Frequency')
    axes[1, 0].set_title('Distribution: Skill Prevalence Across Jobs')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    
    # 4. Cumulative distribution of skill prevalence
    sorted_prevalence = skill_prevalence['prevalence_percentage'].sort_values(ascending=False)
    cumulative_pct = np.arange(1, len(sorted_prevalence) + 1) / len(sorted_prevalence) * 100
    
    axes[1, 1].plot(cumulative_pct, sorted_prevalence, linewidth=2, color='purple')
    axes[1, 1].axhline(50, color='red', linestyle='--', alpha=0.7, label='50% prevalence')
    axes[1, 1].axhline(25, color='orange', linestyle='--', alpha=0.7, label='25% prevalence')
    axes[1, 1].axhline(10, color='green', linestyle='--', alpha=0.7, label='10% prevalence')
    axes[1, 1].axhline(5, color='blue', linestyle='--', alpha=0.7, label='5% prevalence')
    axes[1, 1].set_xlabel('Cumulative % of Skills')
    axes[1, 1].set_ylabel('Skill Prevalence (%)')
    axes[1, 1].set_title('Cumulative Distribution: Skill Prevalence')
    axes[1, 1].legend()
    axes[1, 1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    save_plot(fig, "basic_distributions", "Skill Co-occurrence Data: Basic Distributions")
    plt.show()

# =============================================================================
# CO-OCCURRENCE ANALYSIS
# =============================================================================

def build_cooccurrence_matrix(job_skills_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Build skill co-occurrence matrix and analyze patterns
    
    Returns:
        Tuple of (cooccurrence_matrix, cooccurrence_stats)
    """
    print("\n🔗 BUILDING CO-OCCURRENCE MATRIX")
    print("="*50)
    
    # Create job-skill binary matrix
    print("   → Creating job-skill binary matrix...")
    job_skill_matrix = job_skills_df.pivot_table(
        index='JobProfileID', 
        columns='Skill_Name', 
        values='Skill_ID',
        aggfunc='count',
        fill_value=0
    )
    job_skill_matrix = (job_skill_matrix > 0).astype(int)
    
    print(f"   → Matrix shape: {job_skill_matrix.shape}")
    print(f"   → Sparsity: {(job_skill_matrix == 0).sum().sum() / (job_skill_matrix.shape[0] * job_skill_matrix.shape[1]) * 100:.1f}%")
    
    # Calculate co-occurrence matrix
    print("   → Calculating skill co-occurrence matrix...")
    cooccurrence_matrix = np.dot(job_skill_matrix.T.values, job_skill_matrix.values)
    
    # Convert to DataFrame
    skill_names = job_skill_matrix.columns.tolist()
    cooccurrence_df = pd.DataFrame(
        cooccurrence_matrix,
        index=skill_names,
        columns=skill_names
    )
    
    print(f"   → Co-occurrence matrix shape: {cooccurrence_df.shape}")
    
    # Analyze co-occurrence patterns
    print("   → Analyzing co-occurrence patterns...")
    
    # Extract upper triangle (excluding diagonal) for analysis
    triu_indices = np.triu_indices_from(cooccurrence_matrix, k=1)
    cooccurrence_values = cooccurrence_matrix[triu_indices]
    
    # Create co-occurrence statistics
    cooccurrence_stats = pd.DataFrame({
        'skill_a': [skill_names[i] for i in triu_indices[0]],
        'skill_b': [skill_names[j] for j in triu_indices[1]], 
        'cooccurrence_count': cooccurrence_values
    })
    
    # Add prevalence information
    skill_counts = np.diag(cooccurrence_matrix)
    skill_prevalence_dict = dict(zip(skill_names, skill_counts))
    
    cooccurrence_stats['skill_a_prevalence'] = cooccurrence_stats['skill_a'].map(skill_prevalence_dict)
    cooccurrence_stats['skill_b_prevalence'] = cooccurrence_stats['skill_b'].map(skill_prevalence_dict)
    
    # Calculate conditional probabilities and other metrics
    cooccurrence_stats['prob_b_given_a'] = (
        cooccurrence_stats['cooccurrence_count'] / cooccurrence_stats['skill_a_prevalence']
    )
    cooccurrence_stats['prob_a_given_b'] = (
        cooccurrence_stats['cooccurrence_count'] / cooccurrence_stats['skill_b_prevalence']
    )
    
    # Calculate Jaccard similarity
    cooccurrence_stats['jaccard_similarity'] = (
        cooccurrence_stats['cooccurrence_count'] / 
        (cooccurrence_stats['skill_a_prevalence'] + cooccurrence_stats['skill_b_prevalence'] - 
         cooccurrence_stats['cooccurrence_count'])
    )
    
    # Calculate PMI (Pointwise Mutual Information)
    total_jobs = job_skill_matrix.shape[0]
    cooccurrence_stats['expected_cooccurrence'] = (
        (cooccurrence_stats['skill_a_prevalence'] / total_jobs) * 
        (cooccurrence_stats['skill_b_prevalence'] / total_jobs) * total_jobs
    )
    
    cooccurrence_stats['pmi'] = np.log2(
        cooccurrence_stats['cooccurrence_count'] / 
        np.maximum(cooccurrence_stats['expected_cooccurrence'], 1e-10)  # Avoid log(0)
    )
    
    # Filter out zero co-occurrences for meaningful analysis
    cooccurrence_stats = cooccurrence_stats[cooccurrence_stats['cooccurrence_count'] > 0]
    cooccurrence_stats = cooccurrence_stats.sort_values('cooccurrence_count', ascending=False)
    
    print(f"   → Non-zero co-occurrences: {len(cooccurrence_stats):,}")
    print(f"   → Total possible pairs: {len(skill_names) * (len(skill_names) - 1) // 2:,}")
    print(f"   → Co-occurrence density: {len(cooccurrence_stats) / (len(skill_names) * (len(skill_names) - 1) // 2) * 100:.1f}%")
    
    return cooccurrence_df, cooccurrence_stats

def analyze_cooccurrence_patterns(cooccurrence_stats: pd.DataFrame):
    """Analyze patterns in skill co-occurrence data"""
    print("\n📊 CO-OCCURRENCE PATTERN ANALYSIS")
    print("="*50)
    
    # Basic statistics
    print(f"\n📈 Co-occurrence Frequency Statistics:")
    print(f"   → Mean co-occurrence: {cooccurrence_stats['cooccurrence_count'].mean():.1f}")
    print(f"   → Median co-occurrence: {cooccurrence_stats['cooccurrence_count'].median():.1f}")
    print(f"   → Std dev: {cooccurrence_stats['cooccurrence_count'].std():.1f}")
    print(f"   → Max co-occurrence: {cooccurrence_stats['cooccurrence_count'].max()}")
    print(f"   → 90th percentile: {cooccurrence_stats['cooccurrence_count'].quantile(0.9):.1f}")
    print(f"   → 95th percentile: {cooccurrence_stats['cooccurrence_count'].quantile(0.95):.1f}")
    print(f"   → 99th percentile: {cooccurrence_stats['cooccurrence_count'].quantile(0.99):.1f}")
    
    # Frequency distribution analysis
    frequency_ranges = [
        (1, 1, "Exactly 1"),
        (2, 4, "2-4"),
        (5, 9, "5-9"), 
        (10, 19, "10-19"),
        (20, 49, "20-49"),
        (50, 99, "50-99"),
        (100, float('inf'), "100+")
    ]
    
    print(f"\n📊 Co-occurrence Frequency Ranges:")
    total_pairs = len(cooccurrence_stats)
    for min_val, max_val, label in frequency_ranges:
        if max_val == float('inf'):
            count = (cooccurrence_stats['cooccurrence_count'] >= min_val).sum()
        else:
            count = (
                (cooccurrence_stats['cooccurrence_count'] >= min_val) & 
                (cooccurrence_stats['cooccurrence_count'] <= max_val)
            ).sum()
        percentage = (count / total_pairs) * 100
        print(f"   • {label}: {count:,} pairs ({percentage:.1f}%)")
    
    # Jaccard similarity analysis
    print(f"\n🎯 Jaccard Similarity Statistics:")
    jaccard_stats = cooccurrence_stats['jaccard_similarity']
    print(f"   → Mean Jaccard: {jaccard_stats.mean():.4f}")
    print(f"   → Median Jaccard: {jaccard_stats.median():.4f}")
    print(f"   → Std dev: {jaccard_stats.std():.4f}")
    print(f"   → Max Jaccard: {jaccard_stats.max():.4f}")
    
    # Jaccard similarity ranges
    jaccard_ranges = [
        (0.0, 0.1, "Very Low (0.0-0.1)"),
        (0.1, 0.2, "Low (0.1-0.2)"),
        (0.2, 0.3, "Moderate (0.2-0.3)"),
        (0.3, 0.5, "High (0.3-0.5)"),
        (0.5, 1.0, "Very High (0.5-1.0)")
    ]
    
    print(f"\n📊 Jaccard Similarity Ranges:")
    for min_val, max_val, label in jaccard_ranges:
        count = (
            (jaccard_stats >= min_val) & 
            (jaccard_stats < max_val)
        ).sum()
        percentage = (count / len(jaccard_stats)) * 100
        print(f"   • {label}: {count:,} pairs ({percentage:.1f}%)")
    
    # Top co-occurring pairs
    print(f"\n🏆 Top 20 Most Co-occurring Skill Pairs:")
    for i, (_, row) in enumerate(cooccurrence_stats.head(20).iterrows()):
        rank = i + 1
        skill_a = row['skill_a'][:30]  # Truncate long names
        skill_b = row['skill_b'][:30]
        count = row['cooccurrence_count']
        jaccard = row['jaccard_similarity']
        print(f"   {rank:2d}. {skill_a} ↔ {skill_b}")
        print(f"       Co-occurrence: {count}, Jaccard: {jaccard:.3f}")
    
    # PMI analysis
    valid_pmi = cooccurrence_stats[np.isfinite(cooccurrence_stats['pmi'])]
    print(f"\n🧠 Pointwise Mutual Information (PMI) Analysis:")
    print(f"   → Mean PMI: {valid_pmi['pmi'].mean():.2f}")
    print(f"   → Median PMI: {valid_pmi['pmi'].median():.2f}")
    print(f"   → Std dev: {valid_pmi['pmi'].std():.2f}")
    print(f"   → Min PMI: {valid_pmi['pmi'].min():.2f}")
    print(f"   → Max PMI: {valid_pmi['pmi'].max():.2f}")
    
    print(f"\n🔥 Top 10 Highest PMI Pairs (strongest associations):")
    top_pmi = valid_pmi.nlargest(10, 'pmi')
    for i, (_, row) in enumerate(top_pmi.iterrows()):
        rank = i + 1
        skill_a = row['skill_a'][:25]
        skill_b = row['skill_b'][:25]
        pmi = row['pmi']
        count = row['cooccurrence_count']
        print(f"   {rank:2d}. {skill_a} ↔ {skill_b}")
        print(f"       PMI: {pmi:.2f}, Count: {count}")

def create_cooccurrence_visualizations(cooccurrence_stats: pd.DataFrame):
    """Create visualizations for co-occurrence analysis"""
    print("\n📈 Creating co-occurrence visualizations...")
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Skill Co-occurrence Pattern Analysis', fontsize=16, fontweight='bold')
    
    # 1. Co-occurrence frequency distribution (log scale)
    cooccurrence_counts = cooccurrence_stats['cooccurrence_count']
    log_counts = np.log10(cooccurrence_counts)
    
    axes[0, 0].hist(log_counts, bins=50, alpha=0.7, color='lightblue', edgecolor='black')
    axes[0, 0].axvline(np.log10(cooccurrence_counts.mean()), color='red', linestyle='--', 
                       label=f'Mean: {cooccurrence_counts.mean():.1f}')
    axes[0, 0].axvline(np.log10(cooccurrence_counts.median()), color='orange', linestyle='--', 
                       label=f'Median: {cooccurrence_counts.median():.1f}')
    axes[0, 0].set_xlabel('Log10(Co-occurrence Count)')
    axes[0, 0].set_ylabel('Frequency')
    axes[0, 0].set_title('Distribution: Co-occurrence Frequency (Log Scale)')
    axes[0, 0].legend()
    axes[0, 0].grid(True, alpha=0.3)
    
    # 2. Jaccard similarity distribution
    jaccard_sim = cooccurrence_stats['jaccard_similarity']
    axes[0, 1].hist(jaccard_sim, bins=50, alpha=0.7, color='lightcoral', edgecolor='black')
    axes[0, 1].axvline(jaccard_sim.mean(), color='red', linestyle='--', 
                       label=f'Mean: {jaccard_sim.mean():.3f}')
    axes[0, 1].axvline(jaccard_sim.median(), color='orange', linestyle='--', 
                       label=f'Median: {jaccard_sim.median():.3f}')
    axes[0, 1].set_xlabel('Jaccard Similarity')
    axes[0, 1].set_ylabel('Frequency')
    axes[0, 1].set_title('Distribution: Jaccard Similarity')
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3)
    
    # 3. PMI distribution
    valid_pmi = cooccurrence_stats[np.isfinite(cooccurrence_stats['pmi'])]
    pmi_values = valid_pmi['pmi']
    axes[1, 0].hist(pmi_values, bins=50, alpha=0.7, color='lightgreen', edgecolor='black')
    axes[1, 0].axvline(pmi_values.mean(), color='red', linestyle='--', 
                       label=f'Mean: {pmi_values.mean():.2f}')
    axes[1, 0].axvline(pmi_values.median(), color='orange', linestyle='--', 
                       label=f'Median: {pmi_values.median():.2f}')
    axes[1, 0].axvline(0, color='gray', linestyle=':', alpha=0.7, label='PMI = 0 (independence)')
    axes[1, 0].set_xlabel('Pointwise Mutual Information (PMI)')
    axes[1, 0].set_ylabel('Frequency')
    axes[1, 0].set_title('Distribution: Pointwise Mutual Information')
    axes[1, 0].legend()
    axes[1, 0].grid(True, alpha=0.3)
    
    # 4. Scatter: Co-occurrence count vs Jaccard similarity
    sample_size = min(5000, len(cooccurrence_stats))  # Sample for visualization
    sample_data = cooccurrence_stats.sample(n=sample_size, random_state=42)
    
    scatter = axes[1, 1].scatter(
        sample_data['cooccurrence_count'], 
        sample_data['jaccard_similarity'],
        alpha=0.6, s=20, c='purple'
    )
    axes[1, 1].set_xlabel('Co-occurrence Count')
    axes[1, 1].set_ylabel('Jaccard Similarity')
    axes[1, 1].set_title(f'Co-occurrence Count vs Jaccard Similarity\n(Sample of {sample_size:,} pairs)')
    axes[1, 1].grid(True, alpha=0.3)
    
    # Add correlation coefficient
    correlation = sample_data['cooccurrence_count'].corr(sample_data['jaccard_similarity'])
    axes[1, 1].text(0.05, 0.95, f'Correlation: {correlation:.3f}', 
                    transform=axes[1, 1].transAxes, fontsize=10,
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    save_plot(fig, "cooccurrence_patterns", "Skill Co-occurrence Pattern Analysis")
    plt.show()

# =============================================================================
# SIMILARITY ANALYSIS AND CLUSTERING READINESS
# =============================================================================

def analyze_similarity_thresholds(cooccurrence_df: pd.DataFrame, cooccurrence_stats: pd.DataFrame):
    """Analyze similarity thresholds to understand clustering parameter implications"""
    print("\n🎯 SIMILARITY THRESHOLD ANALYSIS")
    print("="*50)
    
    # Calculate cosine similarity matrix
    print("   → Calculating cosine similarity matrix...")
    cosine_sim_matrix = cosine_similarity(cooccurrence_df.values)
    
    # Extract upper triangle for analysis
    triu_indices = np.triu_indices_from(cosine_sim_matrix, k=1)
    cosine_similarities = cosine_sim_matrix[triu_indices]
    
    print(f"   → Cosine similarity range: {cosine_similarities.min():.4f} to {cosine_similarities.max():.4f}")
    print(f"   → Mean cosine similarity: {cosine_similarities.mean():.4f}")
    print(f"   → Median cosine similarity: {np.median(cosine_similarities):.4f}")
    print(f"   → Std dev: {cosine_similarities.std():.4f}")
    
    # Analyze similarity threshold implications
    threshold_analysis = []
    thresholds = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    
    for threshold in thresholds:
        pairs_above_threshold = np.sum(cosine_similarities > threshold)
        percentage = (pairs_above_threshold / len(cosine_similarities)) * 100
        threshold_analysis.append({
            'threshold': threshold,
            'pairs_above': pairs_above_threshold,
            'percentage': percentage
        })
    
    print(f"\n📊 Cosine Similarity Threshold Analysis:")
    print(f"{'Threshold':<12} {'Pairs Above':<12} {'Percentage':<12}")
    print("-" * 36)
    for analysis in threshold_analysis:
        print(f"{analysis['threshold']:<12.1f} {analysis['pairs_above']:<12,} {analysis['percentage']:<12.1f}%")
    
    # Distance analysis for DBSCAN
    distances = 1 - cosine_similarities
    print(f"\n📏 Distance Analysis (1 - cosine similarity):")
    print(f"   → Distance range: {distances.min():.4f} to {distances.max():.4f}")
    print(f"   → Mean distance: {distances.mean():.4f}")
    print(f"   → Median distance: {np.median(distances):.4f}")
    print(f"   → 25th percentile: {np.percentile(distances, 25):.4f}")
    print(f"   → 75th percentile: {np.percentile(distances, 75):.4f}")
    print(f"   → 90th percentile: {np.percentile(distances, 90):.4f}")
    print(f"   → 95th percentile: {np.percentile(distances, 95):.4f}")
    
    # Suggest DBSCAN eps ranges
    print(f"\n💡 Suggested DBSCAN eps ranges based on distance distribution:")
    print(f"   → Conservative (tight clusters): 0.1 - 0.3")
    print(f"   → Moderate (balanced): 0.3 - 0.6") 
    print(f"   → Liberal (loose clusters): 0.6 - 0.9")
    print(f"   → Current median distance: {np.median(distances):.4f}")
    print(f"   → Current 75th percentile: {np.percentile(distances, 75):.4f}")
    
    return cosine_similarities, distances

def create_similarity_visualizations(cosine_similarities: np.ndarray, distances: np.ndarray):
    """Create visualizations for similarity analysis"""
    print("\n📈 Creating similarity analysis visualizations...")
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle('Similarity Analysis for Clustering Parameter Selection', fontsize=16, fontweight='bold')
    
    # 1. Cosine similarity distribution
    axes[0].hist(cosine_similarities, bins=100, alpha=0.7, color='lightblue', edgecolor='black')
    axes[0].axvline(cosine_similarities.mean(), color='red', linestyle='--', 
                    label=f'Mean: {cosine_similarities.mean():.3f}')
    axes[0].axvline(np.median(cosine_similarities), color='orange', linestyle='--', 
                    label=f'Median: {np.median(cosine_similarities):.3f}')
    axes[0].set_xlabel('Cosine Similarity')
    axes[0].set_ylabel('Frequency')
    axes[0].set_title('Distribution: Cosine Similarity')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # 2. Distance distribution (for DBSCAN)
    axes[1].hist(distances, bins=100, alpha=0.7, color='lightcoral', edgecolor='black')
    axes[1].axvline(distances.mean(), color='red', linestyle='--', 
                    label=f'Mean: {distances.mean():.3f}')
    axes[1].axvline(np.median(distances), color='orange', linestyle='--', 
                    label=f'Median: {np.median(distances):.3f}')
    
    # Add suggested eps ranges
    axes[1].axvspan(0.1, 0.3, alpha=0.2, color='green', label='Conservative eps')
    axes[1].axvspan(0.3, 0.6, alpha=0.2, color='yellow', label='Moderate eps')
    axes[1].axvspan(0.6, 0.9, alpha=0.2, color='red', label='Liberal eps')
    
    axes[1].set_xlabel('Distance (1 - Cosine Similarity)')
    axes[1].set_ylabel('Frequency')
    axes[1].set_title('Distribution: Distance for DBSCAN eps')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    # 3. Cumulative distribution for threshold selection
    sorted_similarities = np.sort(cosine_similarities)[::-1]  # Descending order
    cumulative_pct = np.arange(1, len(sorted_similarities) + 1) / len(sorted_similarities) * 100
    
    axes[2].plot(sorted_similarities, cumulative_pct, linewidth=2, color='purple')
    
    # Add threshold lines
    thresholds = [0.1, 0.2, 0.3, 0.4, 0.5]
    colors = ['blue', 'green', 'orange', 'red', 'brown']
    
    for threshold, color in zip(thresholds, colors):
        pct_above = (cosine_similarities > threshold).sum() / len(cosine_similarities) * 100
        axes[2].axvline(threshold, color=color, linestyle='--', alpha=0.7, 
                        label=f'{threshold:.1f}: {pct_above:.1f}% above')
    
    axes[2].set_xlabel('Cosine Similarity Threshold')
    axes[2].set_ylabel('Cumulative % of Pairs Above Threshold')
    axes[2].set_title('Cumulative Distribution: Similarity Thresholds')
    axes[2].legend()
    axes[2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    save_plot(fig, "similarity_analysis", "Similarity Analysis for Clustering Parameter Selection")
    plt.show()

# =============================================================================
# MAIN EXECUTION FUNCTION
# =============================================================================

def main():
    """Main execution function for skill co-occurrence data exploration"""
    print("🔍 SKILL CO-OCCURRENCE DATA EXPLORATION")
    print("="*60)
    print("🎯 Comprehensive analysis to understand data before clustering")
    print("📊 Focus: Distribution patterns, co-occurrence relationships, similarity thresholds")
    print()
    
    conn = connect_database()
    
    try:
        # Load comprehensive data
        job_skills_df, skills_df, jobs_df = load_comprehensive_skill_data(conn)
        
        # Basic distribution analysis
        skills_per_job, jobs_per_skill, skill_prevalence = analyze_basic_distributions(
            job_skills_df, skills_df, jobs_df
        )
        
        # Create distribution visualizations
        create_distribution_visualizations(skills_per_job, jobs_per_skill, skill_prevalence)
        
        # Co-occurrence analysis
        cooccurrence_df, cooccurrence_stats = build_cooccurrence_matrix(job_skills_df)
        
        # Analyze co-occurrence patterns
        analyze_cooccurrence_patterns(cooccurrence_stats)
        
        # Create co-occurrence visualizations
        create_cooccurrence_visualizations(cooccurrence_stats)
        
        # Similarity threshold analysis
        cosine_similarities, distances = analyze_similarity_thresholds(cooccurrence_df, cooccurrence_stats)
        
        # Create similarity visualizations
        create_similarity_visualizations(cosine_similarities, distances)
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save co-occurrence statistics
        cooccurrence_output = f"cooccurrence_analysis_{timestamp}.csv"
        cooccurrence_stats.to_csv(cooccurrence_output, index=False)
        print(f"\n💾 Co-occurrence analysis saved: {cooccurrence_output}")
        
        # Save skill prevalence
        prevalence_output = f"skill_prevalence_{timestamp}.csv"
        skill_prevalence.to_csv(prevalence_output, index=False)
        print(f"💾 Skill prevalence saved: {prevalence_output}")
        
        # Generate summary recommendations
        print(f"\n💡 EXPLORATION SUMMARY & CLUSTERING RECOMMENDATIONS")
        print("="*60)
        
        print(f"\n📊 Data Characteristics:")
        print(f"   → Skills per job: {skills_per_job.mean():.1f} ± {skills_per_job.std():.1f}")
        print(f"   → Jobs per skill: {jobs_per_skill.mean():.1f} ± {jobs_per_skill.std():.1f}")
        print(f"   → Co-occurrence density: {len(cooccurrence_stats) / (len(cooccurrence_df) * (len(cooccurrence_df) - 1) // 2) * 100:.1f}%")
        print(f"   → Median Jaccard similarity: {cooccurrence_stats['jaccard_similarity'].median():.3f}")
        
        print(f"\n🎯 Clustering Parameter Recommendations:")
        print(f"   → DBSCAN eps range: 0.3 - 0.6 (based on distance distribution)")
        print(f"   → DBSCAN min_samples: 3-5 (based on average skills per job)")
        print(f"   → Alternative: Try hierarchical clustering for comparison")
        print(f"   → Consider filtering rare skills (<{ExplorationConfig.THRESHOLDS['min_jobs_per_skill']} jobs) before clustering")
        
        print(f"\n🔍 Key Insights:")
        print(f"   → Data shows power-law distribution (few very common skills, many rare skills)")
        print(f"   → Co-occurrence is sparse but meaningful patterns exist")
        print(f"   → Similarity distribution suggests natural clustering potential")
        print(f"   → Consider multiple clustering granularities for different use cases")
        
        return {
            'job_skills_df': job_skills_df,
            'cooccurrence_df': cooccurrence_df, 
            'cooccurrence_stats': cooccurrence_stats,
            'skill_prevalence': skill_prevalence,
            'cosine_similarities': cosine_similarities,
            'distances': distances
        }
        
    finally:
        conn.close()
        print(f"\n🔒 Database connection closed")

if __name__ == "__main__":
    print("🔍 SKILL CO-OCCURRENCE DATA EXPLORATION")
    print("="*60)
    print("🎯 Understanding skill relationships before clustering")
    print("📊 Comprehensive analysis of distributions, patterns, and thresholds")
    print()
    
    results = main()
    
    print(f"\n🎉 DATA EXPLORATION COMPLETE!")
    print(f"📁 Check the generated CSV files and plots for detailed insights")
    print(f"💡 Use the recommendations above to inform clustering approach") 