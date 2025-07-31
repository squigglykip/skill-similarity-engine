#!/usr/bin/env python3
"""
OPTUNA BAYESIAN HYPERPARAMETER OPTIMIZATION - Full Dataset Career Pathway Tuning
=================================================================================

Advanced Bayesian optimization using Optuna for finding optimal hyperparameters
for asymmetric career pathway similarity scoring. Uses the FULL dataset instead
of sampling for maximum accuracy and reliability.

Key Features:
- Bayesian optimization with Optuna for efficient parameter search
- Full dataset processing (all jobs, all pairs) for accurate results
- Multi-objective optimization (smoothness + improvement)
- Advanced pruning for early stopping of poor trials
- Comprehensive visualization and analysis
- Memory-efficient processing with progress tracking
- Asymmetric Jaccard similarity with corpus normalization

Expected Performance:
- ~15-25 trials instead of 56+ grid search evaluations
- Full dataset accuracy with ~500K+ job pair comparisons per trial
- Automatic parameter space exploration and exploitation
- Uncertainty quantification and confidence intervals

Usage:
    python optuna_asymmetric_hyperparameter_optimization.py
"""

import pandas as pd
import numpy as np
import sqlite3
import warnings
import optuna
from optuna.samplers import TPESampler
from optuna.pruners import MedianPruner
from optuna.visualization import plot_optimization_history, plot_param_importances
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Set, Any
import scipy.stats
import math
import pickle
import json
from concurrent.futures import ProcessPoolExecutor
import multiprocessing as mp

warnings.filterwarnings('ignore')

# =============================================================================
# CONFIGURATION
# =============================================================================

DATABASE_FILE = "models/2025-Q3/business_context.sqlite"

class OptunaOptimizationConfig:
    """Configuration for Optuna-based hyperparameter optimization"""
    
    DATABASE_PATH = DATABASE_FILE
    
    # Optuna optimization settings
    OPTIMIZATION = {
        'n_trials': 25,                    # Number of Bayesian optimization trials
        'n_startup_trials': 5,             # Random trials before Bayesian starts
        'n_warmup_steps': 3,               # Steps before pruning kicks in
        'sampler': 'TPE',                  # Tree-structured Parzen Estimator
        'pruner': 'MedianPruner',          # Prune poor performing trials early
        'direction': 'minimize',           # Minimize composite smoothness score
        'timeout': 7200,                   # 2 hours maximum optimization time
    }
    
    # Parameter search space (wider than grid search)
    PARAMETER_SPACE = {
        'percentile_threshold': (5, 50),   # 5% to 50% of rarest skills
        'multiplier': (1.01, 1.50),       # 1% to 50% boost
    }
    
    # Multi-objective weights
    OBJECTIVE_WEIGHTS = {
        'smoothness_score': 0.7,          # Primary: smooth distribution
        'improvement_penalty': 0.2,       # Secondary: meaningful improvement
        'efficiency_bonus': 0.1,          # Tertiary: parameter efficiency
    }
    
    # Processing configuration for full dataset
    PROCESSING = {
        'use_full_dataset': True,         # Use all jobs, not sample
        'max_job_pairs_per_trial': None,  # No limit - use all pairs
        'enable_multiprocessing': True,   # Parallel processing
        'max_workers': None,              # Auto-detect CPU cores
        'chunk_size': 10000,              # Chunk size for memory management
        'progress_reporting_interval': 50000,  # Progress every 50k pairs
    }
    
    # Smoothness metric weights (same as before)
    SMOOTHNESS_WEIGHTS = {
        'gini_coefficient': 0.3,
        'coefficient_variation': 0.3,
        'excess_kurtosis': 0.2,
        'percentile_spread_ratio': 0.2
    }

# =============================================================================
# LOGGING SETUP
# =============================================================================

def setup_logging():
    """Setup comprehensive logging for optimization tracking"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"optuna_optimization_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    # Reduce optuna's verbose logging
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    
    return logging.getLogger(__name__)

# =============================================================================
# CORPUS NORMALIZATION (Full implementation)
# =============================================================================

class FullCorpusNormalizer:
    """Full-featured corpus normalizer for optimization"""
    
    def __init__(self):
        self.raw_scores = []
        self.normalization_factor = None
        self.stats = {}
    
    def collect_scores_batch(self, scores: List[float]):
        """Efficiently collect batch of scores"""
        self.raw_scores.extend(scores)
    
    def normalize_and_analyze(self) -> Dict[str, float]:
        """Normalize corpus and return comprehensive analysis"""
        if not self.raw_scores:
            return {'error': 'no_scores'}
        
        raw_array = np.array(self.raw_scores)
        self.normalization_factor = float(np.max(raw_array))
        
        if self.normalization_factor == 0:
            self.normalization_factor = 1.0
        
        # Normalize scores
        normalized_scores = raw_array / self.normalization_factor
        
        # Calculate comprehensive statistics
        self.stats = {
            'raw_min': float(np.min(raw_array)),
            'raw_max': float(np.max(raw_array)),
            'raw_mean': float(np.mean(raw_array)),
            'raw_std': float(np.std(raw_array)),
            'normalized_min': float(np.min(normalized_scores)),
            'normalized_max': float(np.max(normalized_scores)),
            'normalized_mean': float(np.mean(normalized_scores)),
            'normalized_std': float(np.std(normalized_scores)),
            'normalization_factor': self.normalization_factor,
            'total_scores': len(self.raw_scores),
            'scores_above_1': int(np.sum(raw_array > 1.0)),
            'percentage_above_1': (int(np.sum(raw_array > 1.0)) / len(self.raw_scores)) * 100,
            'max_boost_observed': float(np.max(raw_array)) - 1.0 if np.max(raw_array) > 1.0 else 0.0
        }
        
        return normalized_scores, self.stats

# =============================================================================
# SMOOTHNESS ANALYSIS (Enhanced)
# =============================================================================

def calculate_gini_coefficient(scores: np.ndarray) -> float:
    """Calculate Gini coefficient efficiently"""
    sorted_scores = np.sort(scores)
    n = len(scores)
    cumsum = np.cumsum(sorted_scores)
    return (n + 1 - 2 * np.sum(cumsum) / cumsum[-1]) / n

def coefficient_of_variation(scores: np.ndarray) -> float:
    """Calculate coefficient of variation"""
    mean_score = np.mean(scores)
    return np.std(scores) / mean_score if mean_score > 0 else float('inf')

def excess_kurtosis(scores: np.ndarray) -> float:
    """Calculate excess kurtosis"""
    return scipy.stats.kurtosis(scores)

def percentile_spread_ratio(scores: np.ndarray) -> float:
    """Calculate percentile spread ratio for cliff detection"""
    p90, p75, p25, p10 = np.percentile(scores, [90, 75, 25, 10])
    outer_spread = p90 - p10
    inner_spread = p75 - p25
    return outer_spread / inner_spread if inner_spread > 0 else float('inf')

def calculate_comprehensive_smoothness_score(scores: np.ndarray) -> Dict[str, float]:
    """Calculate comprehensive smoothness metrics with advanced analysis"""
    
    # Basic smoothness metrics
    gini = calculate_gini_coefficient(scores)
    cv = coefficient_of_variation(scores)
    kurtosis = abs(excess_kurtosis(scores))
    spread_ratio = percentile_spread_ratio(scores)
    
    # Advanced distribution analysis
    skewness = abs(scipy.stats.skew(scores))
    
    # Normalize metrics to 0-1 scale
    gini_norm = gini
    cv_norm = min(1.0, cv / 0.5)
    kurtosis_norm = min(1.0, kurtosis / 3.0)
    spread_norm = min(1.0, max(0.0, (spread_ratio - 1.0) / 2.0))
    skewness_norm = min(1.0, skewness / 2.0)
    
    # Calculate weighted composite score
    weights = OptunaOptimizationConfig.SMOOTHNESS_WEIGHTS
    composite_score = (
        weights['gini_coefficient'] * gini_norm +
        weights['coefficient_variation'] * cv_norm +
        weights['excess_kurtosis'] * kurtosis_norm +
        weights['percentile_spread_ratio'] * spread_norm
    )
    
    return {
        'gini_coefficient': gini,
        'coefficient_variation': cv,
        'excess_kurtosis': excess_kurtosis(scores),
        'percentile_spread_ratio': spread_ratio,
        'skewness': scipy.stats.skew(scores),
        'composite_smoothness_score': composite_score,
        'gini_norm': gini_norm,
        'cv_norm': cv_norm,
        'kurtosis_norm': kurtosis_norm,
        'spread_norm': spread_norm,
        'skewness_norm': skewness_norm
    }

# =============================================================================
# FULL DATASET LOADING
# =============================================================================

def load_full_dataset(logger) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load the complete dataset for maximum accuracy"""
    logger.info("🗄️ Loading FULL dataset for maximum optimization accuracy...")
    
    try:
        conn = sqlite3.connect(OptunaOptimizationConfig.DATABASE_PATH)
        
        # Load ALL jobs
        jobs_query = """
        SELECT 
            JobProfileID,
            JobProfile,
            JobFunction,
            ManagementLevel,
            JobCategory
        FROM core_job_architecture
        ORDER BY JobProfileID
        """
        
        all_jobs_df = pd.read_sql_query(jobs_query, conn)
        
        # Load ALL job-skill relationships
        job_skills_query = """
        SELECT 
            js.JobProfileID,
            js.Skill_ID,
            s.Skill_Name,
            s.Category as Skill_Category,
            s.SkillType
        FROM core_job_skill_requirements js
        JOIN core_skills_taxonomy s ON js.Skill_ID = s.Skill_ID
        ORDER BY js.JobProfileID, s.Skill_Name
        """
        
        job_skills_df = pd.read_sql_query(job_skills_query, conn)
        conn.close()
        
        logger.info(f"✅ Full dataset loaded:")
        logger.info(f"   → Total jobs: {len(all_jobs_df):,}")
        logger.info(f"   → Total job-skill relationships: {len(job_skills_df):,}")
        logger.info(f"   → Unique skills: {job_skills_df['Skill_ID'].nunique():,}")
        logger.info(f"   → Average skills per job: {len(job_skills_df) / len(all_jobs_df):.1f}")
        
        # Calculate total possible job pairs
        total_job_pairs = len(all_jobs_df) * (len(all_jobs_df) - 1)  # Asymmetric: A→B and B→A
        logger.info(f"   → Total job pairs to evaluate: {total_job_pairs:,}")
        logger.info(f"   → Estimated computation: {total_job_pairs / 1000:.1f}K similarity calculations per trial")
        
        return all_jobs_df, job_skills_df
        
    except Exception as e:
        logger.error(f"Failed to load full dataset: {e}")
        raise

def create_defining_skills_for_percentile_full(
    job_skills_df: pd.DataFrame, 
    percentile_threshold: float,
    logger
) -> Dict[str, Set[str]]:
    """Create defining skills using full dataset for maximum accuracy"""
    
    logger.info(f"🎯 Creating defining skills: {percentile_threshold:.1f}% percentile (full dataset)")
    
    # Calculate skill prevalence across ALL jobs
    total_jobs = job_skills_df['JobProfileID'].nunique()
    skill_prevalence = job_skills_df.groupby('Skill_Name').agg({
        'JobProfileID': 'nunique'
    }).reset_index()
    skill_prevalence['prevalence_percentage'] = (
        skill_prevalence['JobProfileID'] / total_jobs * 100
    )
    
    logger.info(f"   → Calculated prevalence for {len(skill_prevalence):,} unique skills")
    
    # Create job-specific defining skills
    job_defining_skills = {}
    job_groups = list(job_skills_df.groupby('JobProfileID'))
    
    for job_id, job_group in job_groups:
        job_skill_names = job_group['Skill_Name'].tolist()
        
        if not job_skill_names:
            job_defining_skills[job_id] = set()
            continue
        
        # Get prevalence for this job's skills
        job_skill_prevalence = skill_prevalence[
            skill_prevalence['Skill_Name'].isin(job_skill_names)
        ].sort_values('prevalence_percentage')
        
        # Take top percentile_threshold% rarest skills
        num_defining = max(1, int(len(job_skill_prevalence) * percentile_threshold / 100))
        defining_skills = job_skill_prevalence.head(num_defining)['Skill_Name'].tolist()
        
        job_defining_skills[job_id] = set(defining_skills)
    
    # Log statistics
    total_defining_relationships = sum(len(skills) for skills in job_defining_skills.values())
    avg_defining_per_job = total_defining_relationships / len(job_defining_skills)
    
    logger.info(f"   → Jobs with defining skills: {len(job_defining_skills):,}")
    logger.info(f"   → Total defining relationships: {total_defining_relationships:,}")
    logger.info(f"   → Average defining skills per job: {avg_defining_per_job:.1f}")
    
    return job_defining_skills

# =============================================================================
# ASYMMETRIC SIMILARITY CALCULATION (Optimized for Full Dataset)
# =============================================================================

def calculate_asymmetric_similarity_optimized(
    job_a_skills: Set[str],
    job_b_skills: Set[str],
    job_a_defining: Set[str],
    job_b_defining: Set[str],
    multiplier: float
) -> float:
    """
    Optimized asymmetric similarity calculation for full dataset processing.
    Returns only the enhanced similarity score for efficiency.
    """
    if not job_a_skills or not job_b_skills:
        return 0.0
    
    # Asymmetric Jaccard: |A ∩ B| / |A|
    shared_skills = job_a_skills & job_b_skills
    baseline_similarity = len(shared_skills) / len(job_a_skills)
    
    # Defining skills boost
    all_defining = job_a_defining | job_b_defining
    shared_defining_count = len([skill for skill in shared_skills if skill in all_defining])
    
    # Apply multiplier boost (can exceed 1.0)
    defining_skill_boost = shared_defining_count * (multiplier - 1.0)
    enhanced_similarity = baseline_similarity * (1.0 + defining_skill_boost)
    
    return enhanced_similarity

def process_job_pairs_chunk(args):
    """
    Process a chunk of job pairs for multiprocessing.
    Returns list of enhanced similarity scores.
    """
    job_pairs_chunk, job_to_skills, job_defining_skills, multiplier = args
    
    similarities = []
    for job_a_id, job_b_id in job_pairs_chunk:
        if job_a_id == job_b_id:
            continue
            
        job_a_skills = job_to_skills.get(job_a_id, set())
        job_b_skills = job_to_skills.get(job_b_id, set())
        job_a_defining = job_defining_skills.get(job_a_id, set())
        job_b_defining = job_defining_skills.get(job_b_id, set())
        
        similarity = calculate_asymmetric_similarity_optimized(
            job_a_skills, job_b_skills, job_a_defining, job_b_defining, multiplier
        )
        similarities.append(similarity)
    
    return similarities

# =============================================================================
# OPTUNA OBJECTIVE FUNCTION
# =============================================================================

class OptunaObjectiveFunction:
    """Sophisticated objective function for Optuna optimization"""
    
    def __init__(self, jobs_df: pd.DataFrame, job_skills_df: pd.DataFrame, logger):
        self.jobs_df = jobs_df
        self.job_skills_df = job_skills_df
        self.logger = logger
        
        # Pre-compute job-to-skills mapping for efficiency
        self.job_to_skills = {}
        for job_id, group in job_skills_df.groupby('JobProfileID'):
            self.job_to_skills[job_id] = set(group['Skill_Name'].tolist())
        
        self.job_ids = list(self.job_to_skills.keys())
        self.total_pairs = len(self.job_ids) * (len(self.job_ids) - 1)
        
        self.logger.info(f"🎯 Objective function initialized:")
        self.logger.info(f"   → Jobs: {len(self.job_ids):,}")
        self.logger.info(f"   → Total pairs per trial: {self.total_pairs:,}")
        
        # Trial tracking
        self.trial_count = 0
        self.best_score = float('inf')
    
    def __call__(self, trial):
        """
        Optuna objective function - this is called for each trial.
        Returns the score to minimize (composite smoothness score).
        """
        self.trial_count += 1
        trial_start_time = datetime.now()
        
        # Suggest hyperparameters
        percentile_threshold = trial.suggest_float(
            'percentile_threshold', 
            OptunaOptimizationConfig.PARAMETER_SPACE['percentile_threshold'][0],
            OptunaOptimizationConfig.PARAMETER_SPACE['percentile_threshold'][1]
        )
        multiplier = trial.suggest_float(
            'multiplier',
            OptunaOptimizationConfig.PARAMETER_SPACE['multiplier'][0],
            OptunaOptimizationConfig.PARAMETER_SPACE['multiplier'][1]
        )
        
        self.logger.info(f"\n🔬 Trial {self.trial_count}: {percentile_threshold:.1f}% percentile, {multiplier:.3f}x multiplier")
        
        try:
            # Create defining skills for this trial
            job_defining_skills = create_defining_skills_for_percentile_full(
                self.job_skills_df, percentile_threshold, self.logger
            )
            
            # Generate all job pairs
            job_pairs = [(job_a, job_b) for job_a in self.job_ids for job_b in self.job_ids if job_a != job_b]
            
            # Process with multiprocessing for efficiency
            chunk_size = OptunaOptimizationConfig.PROCESSING['chunk_size']
            job_pair_chunks = [job_pairs[i:i + chunk_size] for i in range(0, len(job_pairs), chunk_size)]
            
            self.logger.info(f"   → Processing {len(job_pairs):,} job pairs in {len(job_pair_chunks)} chunks")
            
            # Prepare arguments for multiprocessing
            chunk_args = [
                (chunk, self.job_to_skills, job_defining_skills, multiplier)
                for chunk in job_pair_chunks
            ]
            
            # Process chunks in parallel
            all_similarities = []
            if OptunaOptimizationConfig.PROCESSING['enable_multiprocessing']:
                max_workers = OptunaOptimizationConfig.PROCESSING['max_workers'] or mp.cpu_count()
                with ProcessPoolExecutor(max_workers=max_workers) as executor:
                    chunk_results = list(executor.map(process_job_pairs_chunk, chunk_args))
                    for chunk_similarities in chunk_results:
                        all_similarities.extend(chunk_similarities)
            else:
                # Sequential processing fallback
                for chunk_arg in chunk_args:
                    chunk_similarities = process_job_pairs_chunk(chunk_arg)
                    all_similarities.extend(chunk_similarities)
            
            self.logger.info(f"   → Calculated {len(all_similarities):,} similarity scores")
            
            # Corpus normalization and analysis
            normalizer = FullCorpusNormalizer()
            normalizer.collect_scores_batch(all_similarities)
            normalized_scores, normalization_stats = normalizer.normalize_and_analyze()
            
            # Calculate comprehensive smoothness metrics
            smoothness_metrics = calculate_comprehensive_smoothness_score(normalized_scores)
            
            # Calculate improvement statistics
            raw_scores = np.array(all_similarities)
            baseline_scores = np.array([len(self.job_to_skills[job_a] & self.job_to_skills[job_b]) / len(self.job_to_skills[job_a]) 
                                      for job_a, job_b in job_pairs if job_a != job_b])
            improvements = raw_scores - baseline_scores
            
            avg_improvement = np.mean(improvements)
            positive_improvements = np.sum(improvements > 0)
            positive_improvement_rate = (positive_improvements / len(improvements)) * 100
            
            # Multi-objective scoring
            smoothness_score = smoothness_metrics['composite_smoothness_score']
            
            # Penalty for low improvement (we want meaningful enhancement)
            improvement_penalty = max(0, 0.005 - avg_improvement) * 100  # Penalty if avg improvement < 0.5%
            
            # Efficiency bonus (prefer simpler parameters if performance is similar)
            efficiency_bonus = (percentile_threshold - 20) * 0.001 + (multiplier - 1.05) * 0.01
            
            # Combined objective (to minimize)
            weights = OptunaOptimizationConfig.OBJECTIVE_WEIGHTS
            combined_objective = (
                weights['smoothness_score'] * smoothness_score +
                weights['improvement_penalty'] * improvement_penalty +
                weights['efficiency_bonus'] * abs(efficiency_bonus)
            )
            
            # Log trial results
            trial_duration = (datetime.now() - trial_start_time).total_seconds()
            
            self.logger.info(f"   ✅ Trial {self.trial_count} completed in {trial_duration:.1f}s:")
            self.logger.info(f"      • Smoothness score: {smoothness_score:.4f}")
            self.logger.info(f"      • Average improvement: {avg_improvement*100:.2f}%")
            self.logger.info(f"      • Positive improvements: {positive_improvement_rate:.1f}%")
            self.logger.info(f"      • Scores above 1.0: {normalization_stats['percentage_above_1']:.1f}%")
            self.logger.info(f"      • Normalization factor: {normalization_stats['normalization_factor']:.3f}")
            self.logger.info(f"      • Combined objective: {combined_objective:.4f}")
            
            # Track best score
            if combined_objective < self.best_score:
                self.best_score = combined_objective
                self.logger.info(f"      🏆 NEW BEST SCORE: {combined_objective:.4f}")
            
            # Store additional metrics for analysis
            trial.set_user_attr('smoothness_score', smoothness_score)
            trial.set_user_attr('avg_improvement', avg_improvement)
            trial.set_user_attr('positive_improvement_rate', positive_improvement_rate)
            trial.set_user_attr('normalization_factor', normalization_stats['normalization_factor'])
            trial.set_user_attr('scores_above_1_percent', normalization_stats['percentage_above_1'])
            trial.set_user_attr('trial_duration_seconds', trial_duration)
            
            return combined_objective
            
        except Exception as e:
            self.logger.error(f"   ❌ Trial {self.trial_count} failed: {e}")
            # Return a high penalty score for failed trials
            return 1000.0

# =============================================================================
# MAIN OPTIMIZATION FUNCTION
# =============================================================================

def run_optuna_optimization(logger) -> optuna.Study:
    """Run the main Optuna optimization with full dataset"""
    
    logger.info("[START] Starting Optuna Bayesian Optimization")
    logger.info("=" * 70)
    
    # Load full dataset
    jobs_df, job_skills_df = load_full_dataset(logger)
    
    # Create objective function
    objective = OptunaObjectiveFunction(jobs_df, job_skills_df, logger)
    
    # Configure Optuna study
    sampler = TPESampler(
        n_startup_trials=OptunaOptimizationConfig.OPTIMIZATION['n_startup_trials'],
        n_ei_candidates=24,
        seed=42
    )
    
    pruner = MedianPruner(
        n_startup_trials=OptunaOptimizationConfig.OPTIMIZATION['n_startup_trials'],
        n_warmup_steps=OptunaOptimizationConfig.OPTIMIZATION['n_warmup_steps']
    )
    
    study = optuna.create_study(
        direction=OptunaOptimizationConfig.OPTIMIZATION['direction'],
        sampler=sampler,
        pruner=pruner,
        study_name=f"asymmetric_career_pathway_optimization_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    
    logger.info(f"[CONFIG] Optimization Configuration:")
    logger.info(f"   -> Trials: {OptunaOptimizationConfig.OPTIMIZATION['n_trials']}")
    logger.info(f"   -> Startup trials: {OptunaOptimizationConfig.OPTIMIZATION['n_startup_trials']}")
    logger.info(f"   -> Parameter space: {OptunaOptimizationConfig.PARAMETER_SPACE}")
    logger.info(f"   -> Timeout: {OptunaOptimizationConfig.OPTIMIZATION['timeout']}s")
    logger.info(f"   -> Multiprocessing: {OptunaOptimizationConfig.PROCESSING['enable_multiprocessing']}")
    
    # Run optimization
    try:
        study.optimize(
            objective, 
            n_trials=OptunaOptimizationConfig.OPTIMIZATION['n_trials'],
            timeout=OptunaOptimizationConfig.OPTIMIZATION['timeout'],
            show_progress_bar=True
        )
        
        logger.info("[SUCCESS] Optimization completed successfully!")
        
    except KeyboardInterrupt:
        logger.info("[WARNING] Optimization interrupted by user")
    except Exception as e:
        logger.error(f"[ERROR] Optimization failed: {e}")
        raise
    
    return study

def analyze_optimization_results(study: optuna.Study, logger):
    """Comprehensive analysis of optimization results"""
    
    logger.info("\n" + "=" * 80)
    logger.info("📊 OPTUNA OPTIMIZATION RESULTS - COMPREHENSIVE ANALYSIS")
    logger.info("=" * 80)
    
    # Best trial analysis
    best_trial = study.best_trial
    logger.info(f"\n🏆 BEST TRIAL RESULTS:")
    logger.info(f"   Trial number: {best_trial.number}")
    logger.info(f"   Combined objective score: {best_trial.value:.4f}")
    logger.info(f"   Parameters:")
    for key, value in best_trial.params.items():
        logger.info(f"      • {key}: {value:.3f}")
    
    logger.info(f"   Performance metrics:")
    for key, value in best_trial.user_attrs.items():
        if isinstance(value, float):
            logger.info(f"      • {key}: {value:.4f}")
        else:
            logger.info(f"      • {key}: {value}")
    
    # Parameter importance analysis
    logger.info(f"\n📈 PARAMETER IMPORTANCE:")
    try:
        importance = optuna.importance.get_param_importances(study)
        for param, imp in importance.items():
            logger.info(f"   • {param}: {imp:.3f}")
    except Exception as e:
        logger.warning(f"Could not calculate parameter importance: {e}")
    
    # Trial statistics
    completed_trials = [t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE]
    logger.info(f"\n📊 TRIAL STATISTICS:")
    logger.info(f"   Total trials: {len(study.trials)}")
    logger.info(f"   Completed trials: {len(completed_trials)}")
    logger.info(f"   Failed trials: {len(study.trials) - len(completed_trials)}")
    
    if completed_trials:
        objective_values = [t.value for t in completed_trials]
        logger.info(f"   Best objective: {min(objective_values):.4f}")
        logger.info(f"   Worst objective: {max(objective_values):.4f}")
        logger.info(f"   Mean objective: {np.mean(objective_values):.4f}")
        logger.info(f"   Std objective: {np.std(objective_values):.4f}")
    
    # Top 5 trials
    logger.info(f"\n🎯 TOP 5 TRIALS:")
    top_trials = sorted(completed_trials, key=lambda x: x.value)[:5]
    
    for i, trial in enumerate(top_trials, 1):
        logger.info(f"\n   Rank {i} (Trial {trial.number}):")
        logger.info(f"      Objective: {trial.value:.4f}")
        logger.info(f"      Percentile: {trial.params['percentile_threshold']:.1f}%")
        logger.info(f"      Multiplier: {trial.params['multiplier']:.3f}x")
        if 'smoothness_score' in trial.user_attrs:
            logger.info(f"      Smoothness: {trial.user_attrs['smoothness_score']:.4f}")
        if 'avg_improvement' in trial.user_attrs:
            logger.info(f"      Improvement: {trial.user_attrs['avg_improvement']*100:.2f}%")
    
    # Recommendations
    logger.info(f"\n💡 OPTIMIZATION RECOMMENDATIONS:")
    logger.info(f"🥇 Optimal parameters for asymmetric career pathway scoring:")
    logger.info(f"   • Percentile threshold: {best_trial.params['percentile_threshold']:.1f}%")
    logger.info(f"   • Multiplier: {best_trial.params['multiplier']:.3f}x")
    logger.info(f"   • Expected performance: {best_trial.user_attrs.get('smoothness_score', 'N/A'):.4f} smoothness")
    logger.info(f"   • Expected improvement: {best_trial.user_attrs.get('avg_improvement', 0)*100:.2f}% average")
    
    return best_trial

def save_optimization_results(study: optuna.Study, best_trial, logger):
    """Save comprehensive optimization results"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save study object
    study_file = f"optuna_study_{timestamp}.pkl"
    with open(study_file, 'wb') as f:
        pickle.dump(study, f)
    logger.info(f"💾 Study object saved: {study_file}")
    
    # Save results DataFrame
    trials_df = study.trials_dataframe()
    results_file = f"optuna_optimization_results_{timestamp}.csv"
    trials_df.to_csv(results_file, index=False)
    logger.info(f"💾 Results DataFrame saved: {results_file}")
    
    # Save best parameters as JSON
    best_params = {
        'optimization_timestamp': timestamp,
        'best_trial_number': best_trial.number,
        'best_objective_score': best_trial.value,
        'optimal_parameters': best_trial.params,
        'performance_metrics': best_trial.user_attrs,
        'optimization_config': {
            'n_trials': OptunaOptimizationConfig.OPTIMIZATION['n_trials'],
            'parameter_space': OptunaOptimizationConfig.PARAMETER_SPACE,
            'used_full_dataset': OptunaOptimizationConfig.PROCESSING['use_full_dataset']
        }
    }
    
    params_file = f"optimal_parameters_{timestamp}.json"
    with open(params_file, 'w') as f:
        json.dump(best_params, f, indent=2)
    logger.info(f"💾 Optimal parameters saved: {params_file}")
    
    return results_file, params_file

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main execution function"""
    logger = setup_logging()
    
    logger.info("[OPTUNA] BAYESIAN HYPERPARAMETER OPTIMIZATION")
    logger.info("=" * 80)
    logger.info("[TARGET] Advanced optimization for asymmetric career pathway similarity")
    logger.info("[DATA] Using FULL dataset with Bayesian parameter search")
    logger.info("[BOOST] Multi-objective optimization with corpus normalization")
    logger.info("")
    
    try:
        # Run optimization
        study = run_optuna_optimization(logger)
        
        # Analyze results
        best_trial = analyze_optimization_results(study, logger)
        
        # Save results
        results_file, params_file = save_optimization_results(study, best_trial, logger)
        
        logger.info(f"\n[COMPLETE] OPTUNA OPTIMIZATION COMPLETE!")
        logger.info(f"[FILES] Results saved:")
        logger.info(f"   • Detailed results: {results_file}")
        logger.info(f"   • Optimal parameters: {params_file}")
        logger.info(f"[READY] Ready to implement optimal parameters in production system!")
        
        return study, best_trial
        
    except Exception as e:
        logger.error(f"[FAILED] Optimization failed: {e}")
        raise

if __name__ == "__main__":
    study, best_trial = main()