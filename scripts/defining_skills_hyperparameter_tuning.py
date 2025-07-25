#!/usr/bin/env python3
"""
HYPERPARAMETER TUNING EXPLORATION - Defining Skills & Gentle Multipliers
========================================================================

Systematic testing of percentile thresholds and multipliers for defining skills
to find optimal balance between differentiation and smoothness.

Purpose: 
- Test different combinations of percentile thresholds (10%-40%) and multipliers (1.05-1.5)
- Use stratified sampling for efficiency while maintaining representative results
- Measure distribution smoothness using multiple statistical metrics
- Output detailed CLI comparison for informed decision making

Philosophy: Data-driven hyperparameter optimization with transparent trade-offs

Usage:
    python hyperparameter_tuning_exploration.py
"""

import pandas as pd
import numpy as np
import sqlite3
import warnings
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Set, Any
import scipy.stats
from sklearn.model_selection import train_test_split
import math
from itertools import product

warnings.filterwarnings('ignore')

# =============================================================================
# CONFIGURATION
# =============================================================================

DATABASE_FILE = "models/2025-Q3/workforce_intelligence.sqlite"

class HyperparameterConfig:
    """Configuration for hyperparameter tuning exploration"""
    
    DATABASE_PATH = DATABASE_FILE
    
    # Hyperparameter ranges to test
    PERCENTILE_THRESHOLDS = [10, 15, 20, 25, 30, 35, 40]  # Top X% of rarest skills
    MULTIPLIERS = [1.05, 1.1, 1.15, 1.2, 1.25, 1.3, 1.4, 1.5]  # Gentle multiplier values
    
    # Stratified sampling configuration
    SAMPLING = {
        'target_sample_size': 10000,  # Target number of job pairs to analyze
        'min_jobs_per_stratum': 50,   # Minimum jobs per job function for stratification
        'random_state': 42
    }
    
    # Smoothness metric weights for composite scoring
    SMOOTHNESS_WEIGHTS = {
        'gini_coefficient': 0.3,      # Distribution equality (0-1, lower better)
        'coefficient_variation': 0.3, # Relative spread (lower better)
        'excess_kurtosis': 0.2,       # Tail behavior (closer to 0 better)
        'percentile_spread_ratio': 0.2 # Cliff effects (closer to 1 better)
    }

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def connect_database():
    """Connect to the workforce intelligence database"""
    try:
        conn = sqlite3.connect(HyperparameterConfig.DATABASE_PATH)
        print(f"✅ Connected to database: {HyperparameterConfig.DATABASE_PATH}")
        return conn
    except sqlite3.OperationalError as e:
        raise FileNotFoundError(f"Could not connect to database: {e}")

def calculate_gini_coefficient(scores: np.ndarray) -> float:
    """
    Calculate Gini coefficient (0 = perfectly equal, 1 = maximally unequal)
    Lower values indicate more even distribution
    """
    sorted_scores = np.sort(scores)
    n = len(scores)
    cumsum = np.cumsum(sorted_scores)
    return (n + 1 - 2 * np.sum(cumsum) / cumsum[-1]) / n

def coefficient_of_variation(scores: np.ndarray) -> float:
    """
    Calculate coefficient of variation (std/mean)
    Lower values indicate less relative spread
    """
    return np.std(scores) / np.mean(scores) if np.mean(scores) > 0 else float('inf')

def excess_kurtosis(scores: np.ndarray) -> float:
    """
    Calculate excess kurtosis (0 = normal, >0 = heavy tails, <0 = light tails)
    Values closer to 0 indicate more normal-like distribution
    """
    return scipy.stats.kurtosis(scores)

def percentile_spread_ratio(scores: np.ndarray) -> float:
    """
    Calculate ratio of outer percentile spread to inner percentile spread
    Values closer to 1 indicate less cliff effects
    """
    p90, p75, p25, p10 = np.percentile(scores, [90, 75, 25, 10])
    outer_spread = p90 - p10
    inner_spread = p75 - p25
    return outer_spread / inner_spread if inner_spread > 0 else float('inf')

def calculate_smoothness_score(scores: np.ndarray) -> Dict[str, float]:
    """
    Calculate comprehensive smoothness metrics and composite score
    Lower composite score = smoother distribution
    """
    # Calculate individual metrics
    gini = calculate_gini_coefficient(scores)
    cv = coefficient_of_variation(scores)
    kurtosis = abs(excess_kurtosis(scores))  # Use absolute value
    spread_ratio = percentile_spread_ratio(scores)
    
    # Normalize metrics to 0-1 scale for combination
    # Gini already 0-1
    gini_norm = gini
    
    # CV: normalize by capping at reasonable maximum
    cv_norm = min(1.0, cv / 0.5)  # Cap at 0.5 CV
    
    # Kurtosis: normalize by capping at 3 (very heavy tails)
    kurtosis_norm = min(1.0, kurtosis / 3.0)
    
    # Spread ratio: normalize by capping at 3 (extreme cliff effects)
    spread_norm = min(1.0, max(0.0, (spread_ratio - 1.0) / 2.0))  # Ideal is 1.0
    
    # Calculate weighted composite score
    weights = HyperparameterConfig.SMOOTHNESS_WEIGHTS
    composite_score = (
        weights['gini_coefficient'] * gini_norm +
        weights['coefficient_variation'] * cv_norm +
        weights['excess_kurtosis'] * kurtosis_norm +
        weights['percentile_spread_ratio'] * spread_norm
    )
    
    return {
        'gini_coefficient': gini,
        'coefficient_variation': cv,
        'excess_kurtosis': excess_kurtosis(scores),  # Keep original sign
        'percentile_spread_ratio': spread_ratio,
        'composite_smoothness_score': composite_score,
        'gini_norm': gini_norm,
        'cv_norm': cv_norm,
        'kurtosis_norm': kurtosis_norm,
        'spread_norm': spread_norm
    }

# =============================================================================
# DATA LOADING AND SAMPLING
# =============================================================================

def load_stratified_job_sample(conn) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load stratified sample of jobs for efficient hyperparameter testing
    
    Returns:
        Tuple of (sampled_jobs_df, job_skills_df)
    """
    print("📊 Loading stratified job sample for efficient testing...")
    
    # Load all jobs with function information
    jobs_query = """
    SELECT 
        JobProfileID,
        JobProfile,
        JobFunction,
        JobSubFunction,
        ManagementLevel,
        JobCategory
    FROM jobs
    ORDER BY JobFunction, JobProfileID
    """
    
    all_jobs_df = pd.read_sql_query(jobs_query, conn)
    
    # Load job-skills relationships
    job_skills_query = """
    SELECT 
        js.JobProfileID,
        js.Skill_ID,
        s.Skill_Name,
        s.Category as Skill_Category
    FROM job_skills js
    JOIN skills s ON js.Skill_ID = s.Skill_ID
    """
    
    job_skills_df = pd.read_sql_query(job_skills_query, conn)
    
    print(f"   → Total jobs available: {len(all_jobs_df):,}")
    print(f"   → Total job-skill relationships: {len(job_skills_df):,}")
    
    # Stratify by job function to ensure representative sample
    target_sample = HyperparameterConfig.SAMPLING['target_sample_size']
    min_per_stratum = HyperparameterConfig.SAMPLING['min_jobs_per_stratum']
    
    function_counts = all_jobs_df['JobFunction'].value_counts()
    eligible_functions = function_counts[function_counts >= min_per_stratum].index
    
    print(f"   → Job functions with ≥{min_per_stratum} jobs: {len(eligible_functions)}")
    
    # Calculate sample size per function (proportional allocation)
    eligible_jobs = all_jobs_df[all_jobs_df['JobFunction'].isin(eligible_functions)]
    total_eligible = len(eligible_jobs)
    
    sampled_jobs = []
    for function in eligible_functions:
        function_jobs = eligible_jobs[eligible_jobs['JobFunction'] == function]
        function_proportion = len(function_jobs) / total_eligible
        function_sample_size = max(min_per_stratum, int(target_sample * function_proportion))
        
        # Sample from this function
        function_sample = function_jobs.sample(
            n=min(function_sample_size, len(function_jobs)),
            random_state=HyperparameterConfig.SAMPLING['random_state']
        )
        sampled_jobs.append(function_sample)
    
    sampled_jobs_df = pd.concat(sampled_jobs, ignore_index=True)
    
    print(f"   → Sampled jobs: {len(sampled_jobs_df):,}")
    print(f"   → Sample covers {len(sampled_jobs_df['JobFunction'].unique())} job functions")
    
    # Filter job-skills to sampled jobs only
    sampled_job_skills_df = job_skills_df[
        job_skills_df['JobProfileID'].isin(sampled_jobs_df['JobProfileID'])
    ]
    
    print(f"   → Job-skill relationships for sample: {len(sampled_job_skills_df):,}")
    
    return sampled_jobs_df, sampled_job_skills_df

def create_defining_skills_for_percentile(
    sampled_job_skills_df: pd.DataFrame, 
    percentile_threshold: int
) -> Dict[str, Set[str]]:
    """
    Create job-specific defining skills for a given percentile threshold
    
    Args:
        sampled_job_skills_df: Job-skills relationships for sampled jobs
        percentile_threshold: Top X percentile of skills to consider defining
        
    Returns:
        Dict mapping JobProfileID to Set of defining skill names
    """
    # Calculate skill prevalence across all sampled jobs
    total_jobs = sampled_job_skills_df['JobProfileID'].nunique()
    skill_prevalence = sampled_job_skills_df.groupby('Skill_Name').agg({
        'JobProfileID': 'nunique'
    }).reset_index()
    skill_prevalence['prevalence_percentage'] = (
        skill_prevalence['JobProfileID'] / total_jobs * 100
    )
    
    # Create job-specific defining skills
    job_defining_skills = {}
    
    for job_id in sampled_job_skills_df['JobProfileID'].unique():
        job_skills = sampled_job_skills_df[
            sampled_job_skills_df['JobProfileID'] == job_id
        ]['Skill_Name'].tolist()
        
        if not job_skills:
            job_defining_skills[job_id] = set()
            continue
        
        # Get prevalence for this job's skills
        job_skill_prevalence = skill_prevalence[
            skill_prevalence['Skill_Name'].isin(job_skills)
        ].sort_values('prevalence_percentage')
        
        # Take top percentile_threshold% rarest skills
        num_defining = max(1, len(job_skill_prevalence) * percentile_threshold // 100)
        defining_skills = job_skill_prevalence.head(num_defining)['Skill_Name'].tolist()
        
        job_defining_skills[job_id] = set(defining_skills)
    
    return job_defining_skills

# =============================================================================
# SIMILARITY CALCULATION WITH HYPERPARAMETERS
# =============================================================================

def calculate_similarity_with_params(
    job_a_skills: Set[str],
    job_b_skills: Set[str],
    job_a_defining: Set[str],
    job_b_defining: Set[str],
    multiplier: float
) -> Dict[str, float]:
    """
    Calculate job similarity with specific hyperparameters
    
    Returns:
        Dict with baseline and enhanced similarity scores
    """
    if not job_a_skills or not job_b_skills:
        return {
            'baseline_similarity': 0.0,
            'enhanced_similarity': 0.0,
            'improvement': 0.0,
            'shared_defining_count': 0
        }
    
    # Baseline similarity (Jaccard)
    shared_skills = job_a_skills & job_b_skills
    total_skills = job_a_skills | job_b_skills
    baseline_similarity = len(shared_skills) / len(total_skills) if total_skills else 0.0
    
    # Enhanced similarity with defining skills boost
    all_defining = job_a_defining | job_b_defining
    shared_defining = [skill for skill in shared_skills if skill in all_defining]
    
    # Apply multiplier boost
    defining_skill_boost = len(shared_defining) * (multiplier - 1.0)
    enhanced_similarity = baseline_similarity * (1.0 + defining_skill_boost)
    
    # Cap at 1.0 to maintain similarity interpretation
    enhanced_similarity = min(1.0, enhanced_similarity)
    
    return {
        'baseline_similarity': baseline_similarity,
        'enhanced_similarity': enhanced_similarity,
        'improvement': enhanced_similarity - baseline_similarity,
        'shared_defining_count': len(shared_defining)
    }

def test_hyperparameter_combination(
    percentile_threshold: int,
    multiplier: float,
    sampled_jobs_df: pd.DataFrame,
    sampled_job_skills_df: pd.DataFrame
) -> Dict[str, Any]:
    """
    Test specific hyperparameter combination and return metrics
    
    Returns:
        Dict with performance metrics for this combination
    """
    # Create job-to-skills mapping
    job_to_skills = {}
    for job_id in sampled_jobs_df['JobProfileID'].unique():
        job_skills = sampled_job_skills_df[
            sampled_job_skills_df['JobProfileID'] == job_id
        ]['Skill_Name'].tolist()
        job_to_skills[job_id] = set(job_skills)
    
    # Create defining skills for this percentile threshold
    job_defining_skills = create_defining_skills_for_percentile(
        sampled_job_skills_df, percentile_threshold
    )
    
    # Sample job pairs for efficiency (quadratic in nature)
    job_ids = list(job_to_skills.keys())
    
    # For very large samples, subsample job pairs
    if len(job_ids) > 200:  # Limit to prevent explosion
        job_ids = job_ids[:200]
    
    similarities = []
    total_comparisons = 0
    
    # Calculate similarities for representative sample of job pairs
    for i, job_a in enumerate(job_ids):
        for j, job_b in enumerate(job_ids):
            if i >= j:  # Skip self and duplicate pairs
                continue
                
            total_comparisons += 1
            
            # Skip if we have too many comparisons (keep under 20k for speed)
            if total_comparisons > 20000:
                break
            
            job_a_skills = job_to_skills[job_a]
            job_b_skills = job_to_skills[job_b]
            job_a_defining = job_defining_skills.get(job_a, set())
            job_b_defining = job_defining_skills.get(job_b, set())
            
            similarity_result = calculate_similarity_with_params(
                job_a_skills, job_b_skills, job_a_defining, job_b_defining, multiplier
            )
            
            similarities.append(similarity_result)
        
        if total_comparisons > 20000:
            break
    
    # Extract enhanced similarity scores for distribution analysis
    enhanced_scores = np.array([s['enhanced_similarity'] for s in similarities])
    baseline_scores = np.array([s['baseline_similarity'] for s in similarities])
    improvements = np.array([s['improvement'] for s in similarities])
    
    # Calculate smoothness metrics
    smoothness_metrics = calculate_smoothness_score(enhanced_scores)
    
    # Calculate additional performance metrics
    avg_improvement = np.mean(improvements)
    improvement_std = np.std(improvements)
    positive_improvements = np.sum(improvements > 0)
    total_pairs = len(similarities)
    
    # Distribution characteristics
    score_range = enhanced_scores.max() - enhanced_scores.min()
    score_mean = np.mean(enhanced_scores)
    score_median = np.median(enhanced_scores)
    
    return {
        'percentile_threshold': percentile_threshold,
        'multiplier': multiplier,
        'total_job_pairs': total_pairs,
        'avg_improvement': avg_improvement,
        'improvement_std': improvement_std,
        'positive_improvements': positive_improvements,
        'positive_improvement_rate': positive_improvements / total_pairs * 100,
        'score_range': score_range,
        'score_mean': score_mean,
        'score_median': score_median,
        'baseline_mean': np.mean(baseline_scores),
        'baseline_std': np.std(baseline_scores),
        'enhanced_std': np.std(enhanced_scores),
        **smoothness_metrics  # Include all smoothness metrics
    }

# =============================================================================
# HYPERPARAMETER GRID SEARCH
# =============================================================================

def run_hyperparameter_grid_search(
    sampled_jobs_df: pd.DataFrame,
    sampled_job_skills_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Run comprehensive grid search over hyperparameter combinations
    
    Returns:
        DataFrame with results for all combinations tested
    """
    print("🔍 Running hyperparameter grid search...")
    
    percentiles = HyperparameterConfig.PERCENTILE_THRESHOLDS
    multipliers = HyperparameterConfig.MULTIPLIERS
    
    total_combinations = len(percentiles) * len(multipliers)
    print(f"   → Testing {total_combinations} combinations:")
    print(f"   → Percentile thresholds: {percentiles}")
    print(f"   → Multipliers: {multipliers}")
    
    results = []
    combination_count = 0
    
    for percentile, multiplier in product(percentiles, multipliers):
        combination_count += 1
        print(f"   → Testing combination {combination_count}/{total_combinations}: "
              f"{percentile}% percentile, {multiplier}x multiplier")
        
        result = test_hyperparameter_combination(
            percentile, multiplier, sampled_jobs_df, sampled_job_skills_df
        )
        
        results.append(result)
    
    results_df = pd.DataFrame(results)
    
    print(f"✅ Grid search complete! Tested {len(results_df)} combinations")
    
    return results_df

def analyze_hyperparameter_results(results_df: pd.DataFrame) -> None:
    """
    Generate detailed CLI analysis of hyperparameter tuning results
    """
    print("\n" + "="*80)
    print("📊 HYPERPARAMETER TUNING RESULTS - DETAILED ANALYSIS")
    print("="*80)
    
    # Sort by composite smoothness score (lower is better)
    sorted_results = results_df.sort_values('composite_smoothness_score')
    
    print(f"\n🎯 OVERALL SUMMARY")
    print("-" * 50)
    print(f"Total combinations tested: {len(results_df):,}")
    print(f"Job pairs analyzed per combination: {results_df['total_job_pairs'].iloc[0]:,}")
    print(f"Percentile range: {results_df['percentile_threshold'].min()}% - {results_df['percentile_threshold'].max()}%")
    print(f"Multiplier range: {results_df['multiplier'].min():.2f} - {results_df['multiplier'].max():.2f}")
    
    # Top 10 smoothest distributions
    print(f"\n🏆 TOP 10 SMOOTHEST DISTRIBUTIONS (by composite smoothness score)")
    print("-" * 90)
    header = f"{'Rank':<4} {'Percentile':<10} {'Multiplier':<10} {'Smooth Score':<12} {'Avg Improve':<12} {'Positive %':<10} {'Score Range':<12}"
    print(header)
    print("-" * 90)
    
    for i, (_, row) in enumerate(sorted_results.head(10).iterrows()):
        rank = i + 1
        percentile = f"{row['percentile_threshold']}%"
        multiplier = f"{row['multiplier']:.2f}x"
        smooth_score = f"{row['composite_smoothness_score']:.4f}"
        avg_improve = f"{row['avg_improvement']*100:.2f}%"
        positive_rate = f"{row['positive_improvement_rate']:.1f}%"
        score_range = f"{row['score_range']:.4f}"
        
        print(f"{rank:<4} {percentile:<10} {multiplier:<10} {smooth_score:<12} {avg_improve:<12} {positive_rate:<10} {score_range:<12}")
    
    # Detailed metrics for top 5
    print(f"\n📋 DETAILED METRICS FOR TOP 5 COMBINATIONS")
    print("-" * 80)
    
    for i, (_, row) in enumerate(sorted_results.head(5).iterrows()):
        rank = i + 1
        print(f"\n🥇 RANK {rank}: {row['percentile_threshold']}% percentile, {row['multiplier']:.2f}x multiplier")
        print(f"   Composite smoothness score: {row['composite_smoothness_score']:.4f} (lower = smoother)")
        print(f"   ")
        print(f"   📈 Performance Metrics:")
        print(f"      • Average improvement: {row['avg_improvement']*100:.2f}% points")
        print(f"      • Improvement std dev: {row['improvement_std']*100:.2f}% points")
        print(f"      • Positive improvements: {row['positive_improvements']:,}/{row['total_job_pairs']:,} ({row['positive_improvement_rate']:.1f}%)")
        print(f"   ")
        print(f"   📊 Distribution Characteristics:")
        print(f"      • Score range: {row['score_range']:.4f} (max - min)")
        print(f"      • Enhanced mean: {row['score_mean']:.4f}")
        print(f"      • Enhanced median: {row['score_median']:.4f}")
        print(f"      • Enhanced std: {row['enhanced_std']:.4f}")
        print(f"      • Baseline mean: {row['baseline_mean']:.4f}")
        print(f"      • Baseline std: {row['baseline_std']:.4f}")
        print(f"   ")
        print(f"   🎯 Smoothness Components:")
        print(f"      • Gini coefficient: {row['gini_coefficient']:.4f} (0=equal, 1=unequal)")
        print(f"      • Coefficient of variation: {row['coefficient_variation']:.4f} (lower=less spread)")
        print(f"      • Excess kurtosis: {row['excess_kurtosis']:.4f} (0=normal, ±=heavy/light tails)")
        print(f"      • Percentile spread ratio: {row['percentile_spread_ratio']:.4f} (1=no cliffs)")
    
    # Analysis by percentile threshold
    print(f"\n📊 ANALYSIS BY PERCENTILE THRESHOLD")
    print("-" * 60)
    
    percentile_analysis = results_df.groupby('percentile_threshold').agg({
        'composite_smoothness_score': ['mean', 'std', 'min'],
        'avg_improvement': 'mean',
        'positive_improvement_rate': 'mean'
    }).round(4)
    
    print(f"{'Percentile':<10} {'Avg Smooth':<12} {'Min Smooth':<12} {'Avg Improve':<12} {'Avg Positive%':<12}")
    print("-" * 60)
    
    for percentile in sorted(results_df['percentile_threshold'].unique()):
        data = percentile_analysis.loc[percentile]
        avg_smooth = f"{data[('composite_smoothness_score', 'mean')]:.4f}"
        min_smooth = f"{data[('composite_smoothness_score', 'min')]:.4f}"
        avg_improve = f"{data[('avg_improvement', 'mean')]*100:.2f}%"
        avg_positive = f"{data[('positive_improvement_rate', 'mean')]:.1f}%"
        
        print(f"{percentile}%{'':<6} {avg_smooth:<12} {min_smooth:<12} {avg_improve:<12} {avg_positive:<12}")
    
    # Analysis by multiplier
    print(f"\n📊 ANALYSIS BY MULTIPLIER")
    print("-" * 60)
    
    multiplier_analysis = results_df.groupby('multiplier').agg({
        'composite_smoothness_score': ['mean', 'std', 'min'],
        'avg_improvement': 'mean',
        'positive_improvement_rate': 'mean'
    }).round(4)
    
    print(f"{'Multiplier':<10} {'Avg Smooth':<12} {'Min Smooth':<12} {'Avg Improve':<12} {'Avg Positive%':<12}")
    print("-" * 60)
    
    for multiplier in sorted(results_df['multiplier'].unique()):
        data = multiplier_analysis.loc[multiplier]
        avg_smooth = f"{data[('composite_smoothness_score', 'mean')]:.4f}"
        min_smooth = f"{data[('composite_smoothness_score', 'min')]:.4f}"
        avg_improve = f"{data[('avg_improvement', 'mean')]*100:.2f}%"
        avg_positive = f"{data[('positive_improvement_rate', 'mean')]:.1f}%"
        
        print(f"{multiplier:.2f}x{'':<4} {avg_smooth:<12} {min_smooth:<12} {avg_improve:<12} {avg_positive:<12}")
    
    # Recommendations
    best_combination = sorted_results.iloc[0]
    print(f"\n💡 RECOMMENDATIONS")
    print("-" * 50)
    print(f"🥇 Best combination for smoothness:")
    print(f"   • Percentile threshold: {best_combination['percentile_threshold']}% (top rarest skills per job)")
    print(f"   • Multiplier: {best_combination['multiplier']:.2f}x (gentle boost for shared defining skills)")
    print(f"   • Expected improvement: {best_combination['avg_improvement']*100:.2f}% points average")
    print(f"   • Smoothness score: {best_combination['composite_smoothness_score']:.4f}")
    
    # Alternative balanced recommendation
    balanced_criteria = (
        (results_df['composite_smoothness_score'] <= results_df['composite_smoothness_score'].quantile(0.2)) &
        (results_df['avg_improvement'] >= results_df['avg_improvement'].quantile(0.5))
    )
    
    if balanced_criteria.any():
        balanced_options = results_df[balanced_criteria].sort_values('avg_improvement', ascending=False)
        if len(balanced_options) > 0:
            balanced_best = balanced_options.iloc[0]
            print(f"\n⚖️  Balanced recommendation (smooth + high improvement):")
            print(f"   • Percentile threshold: {balanced_best['percentile_threshold']}%")
            print(f"   • Multiplier: {balanced_best['multiplier']:.2f}x")
            print(f"   • Expected improvement: {balanced_best['avg_improvement']*100:.2f}% points average")
            print(f"   • Smoothness score: {balanced_best['composite_smoothness_score']:.4f}")

# =============================================================================
# MAIN EXECUTION FUNCTION
# =============================================================================

def main():
    """Main execution function for hyperparameter tuning exploration"""
    print("🔬 HYPERPARAMETER TUNING EXPLORATION")
    print("="*60)
    print("🎯 Testing percentile thresholds and multipliers for optimal similarity scoring")
    print("📊 Focus: Balance between differentiation and distribution smoothness")
    print()
    
    conn = connect_database()
    
    try:
        # Load stratified sample
        sampled_jobs_df, sampled_job_skills_df = load_stratified_job_sample(conn)
        
        # Run grid search
        results_df = run_hyperparameter_grid_search(sampled_jobs_df, sampled_job_skills_df)
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"hyperparameter_tuning_results_{timestamp}.csv"
        results_df.to_csv(output_path, index=False)
        print(f"\n💾 Detailed results saved: {output_path}")
        
        # Generate detailed analysis
        analyze_hyperparameter_results(results_df)
        
        return results_df
        
    finally:
        conn.close()
        print(f"\n🔒 Database connection closed")

if __name__ == "__main__":
    print("🔬 HYPERPARAMETER TUNING EXPLORATION - DEFINING SKILLS OPTIMIZATION")
    print("="*80)
    print("🎯 Finding optimal balance between skill differentiation and smooth distributions")
    print("📊 Testing systematic combinations of percentile thresholds and multipliers")
    print()
    
    results = main()
    
    print(f"\n🎉 HYPERPARAMETER TUNING COMPLETE!")
    print(f"📁 Check the generated CSV for complete numerical results")
    print(f"💡 Use the recommendations above to optimize your similarity scoring parameters") 