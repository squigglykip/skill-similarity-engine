"""
Simple Optuna Similarity Optimizer

Straightforward Bayesian optimization that replaces similarity_parameters.yaml completely.
"""

import os
import sqlite3
import pandas as pd
import numpy as np
import multiprocessing as mp
from pathlib import Path
from datetime import datetime
from typing import Dict, Set, List, Tuple
from concurrent.futures import ProcessPoolExecutor

try:
    import optuna
    from optuna.samplers import TPESampler
    from optuna.pruners import MedianPruner
    import scipy.stats
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False


def calculate_asymmetric_similarity(job_a_skills: Set[str], job_b_skills: Set[str], 
                                  job_a_defining: Set[str], job_b_defining: Set[str], 
                                  multiplier: float) -> float:
    """Calculate enhanced asymmetric similarity"""
    if not job_a_skills or not job_b_skills:
        return 0.0
    
    shared_skills = job_a_skills & job_b_skills
    baseline_similarity = len(shared_skills) / len(job_a_skills)
    
    all_defining = job_a_defining | job_b_defining
    shared_defining_count = len([skill for skill in shared_skills if skill in all_defining])
    
    defining_skill_boost = shared_defining_count * (multiplier - 1.0)
    enhanced_similarity = baseline_similarity * (1.0 + defining_skill_boost)
    
    return enhanced_similarity


def process_job_pairs_chunk(args):
    """Process job pairs chunk for multiprocessing"""
    job_pairs_chunk, job_to_skills, job_defining_skills, multiplier = args
    
    similarities = []
    for job_a_id, job_b_id in job_pairs_chunk:
        if job_a_id == job_b_id:
            continue
            
        job_a_skills = job_to_skills.get(job_a_id, set())
        job_b_skills = job_to_skills.get(job_b_id, set())
        job_a_defining = job_defining_skills.get(job_a_id, set())
        job_b_defining = job_defining_skills.get(job_b_id, set())
        
        similarity = calculate_asymmetric_similarity(
            job_a_skills, job_b_skills, job_a_defining, job_b_defining, multiplier
        )
        similarities.append(similarity)
    
    return similarities


def create_defining_skills_constrained(job_skills_df: pd.DataFrame, percentile_threshold: float, 
                                      max_percentile_cap: float = 50.0) -> Dict[str, Set[str]]:
    """Create defining skills for each job with business constraints"""
    total_jobs = job_skills_df['JobProfileID'].nunique()
    skill_prevalence = job_skills_df.groupby('Skill_Name').agg({
        'JobProfileID': 'nunique'
    }).reset_index()
    skill_prevalence['prevalence_percentage'] = (
        skill_prevalence['JobProfileID'] / total_jobs * 100
    )
    
    job_defining_skills = {}
    for job_id, job_group in job_skills_df.groupby('JobProfileID'):
        job_skill_names = job_group['Skill_Name'].tolist()
        
        if not job_skill_names:
            job_defining_skills[job_id] = set()
            continue
        
        job_skill_prevalence = skill_prevalence[
            skill_prevalence['Skill_Name'].isin(job_skill_names)
        ].sort_values('prevalence_percentage')
        
        # Apply business constraint cap if specified
        effective_percentile = percentile_threshold
        if max_percentile_cap is not None:
            effective_percentile = min(percentile_threshold, max_percentile_cap)
        
        num_defining = max(1, int(len(job_skill_prevalence) * effective_percentile / 100))
        
        # Apply absolute business limits (hard caps)
        num_defining = max(1, min(num_defining, 10))  # min 1, max 10 defining skills
        
        defining_skills = job_skill_prevalence.head(num_defining)['Skill_Name'].tolist()
        job_defining_skills[job_id] = set(defining_skills)
    
    return job_defining_skills


def create_defining_skills(job_skills_df: pd.DataFrame, percentile_threshold: float) -> Dict[str, Set[str]]:
    """Create defining skills for each job (legacy wrapper for backward compatibility)"""
    return create_defining_skills_constrained(job_skills_df, percentile_threshold)


def calculate_smoothness_score(scores: np.ndarray) -> float:
    """Calculate simple smoothness score"""
    gini = calculate_gini_coefficient(scores)
    cv = coefficient_of_variation(scores)
    kurtosis = abs(scipy.stats.kurtosis(scores))
    
    # Simple weighted average
    return float(0.4 * gini + 0.4 * min(1.0, float(cv) / 0.5) + 0.2 * min(1.0, float(kurtosis) / 3.0))


def calculate_gini_coefficient(scores: np.ndarray) -> float:
    """Calculate Gini coefficient"""
    sorted_scores = np.sort(scores)
    n = len(scores)
    cumsum = np.cumsum(sorted_scores)
    return (n + 1 - 2 * np.sum(cumsum) / cumsum[-1]) / n


def coefficient_of_variation(scores: np.ndarray) -> float:
    """Calculate coefficient of variation"""
    mean_score = float(np.mean(scores))
    return float(np.std(scores)) / mean_score if mean_score > 0 else float('inf')


class OptunaSimilarityOptimizer:
    """Simple Optuna optimizer that completely replaces similarity_parameters.yaml"""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.config_path = Path("config/core/similarity_parameters.yaml")
        self.optimization_config_path = Path("config/core/optimization.yaml")
        
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        
        if not OPTUNA_AVAILABLE:
            raise ImportError("Optuna not available. Install with: pip install optuna")
        
        # Suppress Optuna logging to prevent interference with progress bars
        optuna.logging.set_verbosity(optuna.logging.WARNING)
        
        # Load optimization configuration
        self.optimization_config = self._load_optimization_config()
    
    def _load_optimization_config(self) -> dict:
        """Load optimization configuration from YAML file"""
        try:
            import yaml
            with open(self.optimization_config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            return config
        except FileNotFoundError:
            print(f"⚠️  Optimization config not found at {self.optimization_config_path}")
            print("   Using default settings: 25 trials")
            return {
                'optuna': {'max_trials': 25, 'timeout_minutes': 20},
                'parameter_space': {
                    'percentile_threshold': {'min': 5.0, 'max': 50.0},
                    'multiplier': {'min': 1.01, 'max': 1.50}
                }
            }
        except Exception as e:
            print(f"⚠️  Error loading optimization config: {e}")
            print("   Using default settings: 25 trials")
            return {
                'optuna': {'max_trials': 25, 'timeout_minutes': 20},
                'parameter_space': {
                    'percentile_threshold': {'min': 5.0, 'max': 50.0},
                    'multiplier': {'min': 1.01, 'max': 1.50}
                }
            }
    
    def load_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Load jobs and job-skills data"""
        print("🗄️ Loading dataset...")
        
        conn = sqlite3.connect(str(self.db_path))
        
        jobs_df = pd.read_sql_query("""
            SELECT JobProfileID, JobProfile, JobFunction, ManagementLevel, JobCategory
            FROM core_job_architecture
            ORDER BY JobProfileID
        """, conn)
        
        job_skills_df = pd.read_sql_query("""
            SELECT js.JobProfileID, js.Skill_ID, s.Skill_Name, s.Category, s.SkillType
            FROM core_job_skill_requirements js
            JOIN core_skills_taxonomy s ON js.Skill_ID = s.Skill_ID
            ORDER BY js.JobProfileID, s.Skill_Name
        """, conn)
        
        conn.close()
        
        print(f"✅ Loaded {len(jobs_df):,} jobs and {len(job_skills_df):,} job-skill relationships")
        return jobs_df, job_skills_df
    
    def objective_function_stratified(self, trial, job_skills_subset: pd.DataFrame, 
                                     layer_name: str, max_percentile_cap: float):
        """Stratified objective function for specific job size layer"""
        # Get parameter ranges from config
        param_config = self.optimization_config.get('parameter_space', {})
        
        percentile_config = param_config.get('percentile_threshold', {'min': 5.0, 'max': 50.0})
        multiplier_config = param_config.get('multiplier', {'min': 1.01, 'max': 1.50})
        
        # Constrain percentile to business cap for this layer
        max_percentile = min(percentile_config['max'], max_percentile_cap)
        
        percentile_threshold = trial.suggest_float('percentile_threshold', 
                                                 percentile_config['min'], 
                                                 max_percentile)
        multiplier = trial.suggest_float('multiplier', 
                                       multiplier_config['min'], 
                                       multiplier_config['max'])
        
        # Create job-to-skills mapping for this subset
        job_to_skills = {}
        for job_id, group in job_skills_subset.groupby('JobProfileID'):
            job_to_skills[job_id] = set(group['Skill_Name'].tolist())
        
        job_ids = list(job_to_skills.keys())
        
        # Create defining skills with business constraints
        job_defining_skills = create_defining_skills_constrained(
            job_skills_subset, percentile_threshold, max_percentile_cap
        )
        
        # Generate job pairs
        job_pairs = [(job_a, job_b) for job_a in job_ids for job_b in job_ids if job_a != job_b]
        
        if not job_pairs:
            return float('inf')  # Invalid if no pairs
        
        # Process in chunks
        chunk_size = 5000
        job_pair_chunks = [job_pairs[i:i + chunk_size] for i in range(0, len(job_pairs), chunk_size)]
        
        chunk_args = [
            (chunk, job_to_skills, job_defining_skills, multiplier)
            for chunk in job_pair_chunks
        ]
        
        # Process (sequential on Windows for safety)
        all_similarities = []
        for chunk_arg in chunk_args:
            chunk_similarities = process_job_pairs_chunk(chunk_arg)
            all_similarities.extend(chunk_similarities)
        
        if not all_similarities:
            return float('inf')
        
        # Normalize scores using logarithmic scaling
        raw_scores = np.array(all_similarities)
        max_score = np.max(raw_scores)
        
        # Apply logarithmic normalization: log(1 + x) / log(1 + max)
        if max_score > 0:
            normalized_scores = np.log(1 + raw_scores) / np.log(1 + max_score)
        else:
            normalized_scores = raw_scores
        
        # Calculate smoothness
        smoothness_score = calculate_smoothness_score(normalized_scores)
        
        # Calculate improvement
        baseline_scores = np.array([
            len(job_to_skills[job_a] & job_to_skills[job_b]) / len(job_to_skills[job_a])
            for job_a, job_b in job_pairs if job_a != job_b
        ])
        avg_improvement = np.mean(raw_scores - baseline_scores)
        
        # Simple combined objective (to minimize)
        combined_objective = float(smoothness_score - (avg_improvement * 10))  # Encourage improvement
        
        trial.set_user_attr('smoothness_score', smoothness_score)
        trial.set_user_attr('avg_improvement', avg_improvement)
        trial.set_user_attr('normalization_factor', max_score)
        trial.set_user_attr('scores_above_1_percent', (np.sum(raw_scores > 1.0) / len(raw_scores)) * 100)
        
        return combined_objective


    def objective_function(self, trial, jobs_df: pd.DataFrame, job_skills_df: pd.DataFrame):
        """Legacy objective function for backward compatibility"""
        # Get parameter ranges from config
        param_config = self.optimization_config.get('parameter_space', {})
        
        percentile_config = param_config.get('percentile_threshold', {'min': 5.0, 'max': 50.0})
        multiplier_config = param_config.get('multiplier', {'min': 1.01, 'max': 1.50})
        
        percentile_threshold = trial.suggest_float('percentile_threshold', 
                                                 percentile_config['min'], 
                                                 percentile_config['max'])
        multiplier = trial.suggest_float('multiplier', 
                                       multiplier_config['min'], 
                                       multiplier_config['max'])
        
        # Create job-to-skills mapping
        job_to_skills = {}
        for job_id, group in job_skills_df.groupby('JobProfileID'):
            job_to_skills[job_id] = set(group['Skill_Name'].tolist())
        
        job_ids = list(job_to_skills.keys())
        
        # Create defining skills
        job_defining_skills = create_defining_skills(job_skills_df, percentile_threshold)
        
        # Generate job pairs
        job_pairs = [(job_a, job_b) for job_a in job_ids for job_b in job_ids if job_a != job_b]
        
        # Process in chunks
        chunk_size = 5000
        job_pair_chunks = [job_pairs[i:i + chunk_size] for i in range(0, len(job_pairs), chunk_size)]
        
        chunk_args = [
            (chunk, job_to_skills, job_defining_skills, multiplier)
            for chunk in job_pair_chunks
        ]
        
        # Process (sequential on Windows for safety)
        all_similarities = []
        for chunk_arg in chunk_args:
            chunk_similarities = process_job_pairs_chunk(chunk_arg)
            all_similarities.extend(chunk_similarities)
        
        # Normalize scores using logarithmic scaling
        raw_scores = np.array(all_similarities)
        max_score = np.max(raw_scores)
        
        # Apply logarithmic normalization: log(1 + x) / log(1 + max)
        if max_score > 0:
            normalized_scores = np.log(1 + raw_scores) / np.log(1 + max_score)
        else:
            normalized_scores = raw_scores
        
        # Calculate smoothness
        smoothness_score = calculate_smoothness_score(normalized_scores)
        
        # Calculate improvement
        baseline_scores = np.array([
            len(job_to_skills[job_a] & job_to_skills[job_b]) / len(job_to_skills[job_a])
            for job_a, job_b in job_pairs if job_a != job_b
        ])
        avg_improvement = np.mean(raw_scores - baseline_scores)
        
        # Simple combined objective (to minimize)
        combined_objective = float(smoothness_score - (avg_improvement * 10))  # Encourage improvement
        
        trial.set_user_attr('smoothness_score', smoothness_score)
        trial.set_user_attr('avg_improvement', avg_improvement)
        trial.set_user_attr('normalization_factor', max_score)
        trial.set_user_attr('scores_above_1_percent', (np.sum(raw_scores > 1.0) / len(raw_scores)) * 100)
        
        return combined_objective
    
    def run_stratified_optimization(self) -> Dict:
        """Run stratified optimization per job size category"""
        jobs_df, job_skills_df = self.load_data()
        
        # Calculate job skill counts
        job_skill_counts = job_skills_df.groupby('JobProfileID')['Skill_Name'].count().reset_index()
        job_skill_counts.columns = ['JobProfileID', 'skill_count']
        
        # Define business constraint layers
        layers = {
            'small_jobs': {'max_skills': 15, 'max_percentile': 50.0, 'description': '≤15 skills'},
            'medium_jobs': {'max_skills': 30, 'max_percentile': 30.0, 'description': '16-30 skills'},
            'large_jobs': {'max_skills': 50, 'max_percentile': 20.0, 'description': '31-50 skills'},
            'xlarge_jobs': {'max_skills': 999, 'max_percentile': 15.0, 'description': '>50 skills'}
        }
        
        # Get configuration settings
        optuna_config = self.optimization_config.get('optuna', {})
        trials_per_layer = 25  # 25 trials per layer for thorough optimization
        timeout_minutes = optuna_config.get('timeout_minutes', 20)
        
        print(f"🚀 Starting Stratified Optuna Optimization...")
        print(f"   • {trials_per_layer} trials per job size layer")
        print(f"   • {len(layers)} job size categories")
        print(f"   • Total trials: {trials_per_layer * len(layers)}")
        print(f"   • Time limit: {timeout_minutes} minutes")
        print(f"   • Early stopping: MedianPruner enabled")
        print()
        
        # Segment jobs by size
        stratified_results = {}
        total_jobs_processed = 0
        layer_names = list(layers.keys())
        
        for i, (layer_name, layer_config) in enumerate(layers.items()):
            # Filter jobs for this layer
            if layer_name == 'small_jobs':
                layer_jobs = job_skill_counts[job_skill_counts['skill_count'] <= 15]['JobProfileID']
            elif layer_name == 'medium_jobs':
                layer_jobs = job_skill_counts[
                    (job_skill_counts['skill_count'] > 15) & 
                    (job_skill_counts['skill_count'] <= 30)
                ]['JobProfileID']
            elif layer_name == 'large_jobs':
                layer_jobs = job_skill_counts[
                    (job_skill_counts['skill_count'] > 30) & 
                    (job_skill_counts['skill_count'] <= 50)
                ]['JobProfileID']
            else:  # xlarge_jobs
                layer_jobs = job_skill_counts[job_skill_counts['skill_count'] > 50]['JobProfileID']
            
            if len(layer_jobs) == 0:
                print(f"   ⚠️  No jobs found for {layer_name} ({layer_config['description']}) - skipping")
                continue
                
            # Filter job skills for this layer
            layer_job_skills = job_skills_df[job_skills_df['JobProfileID'].isin(layer_jobs)]
            
            total_jobs_processed += len(layer_jobs)
            
            # Create study for this layer with enhanced early stopping
            sampler_config = optuna_config.get('sampler', {})
            pruner_config = optuna_config.get('pruner', {})
            
            study = optuna.create_study(
                direction='minimize',
                sampler=TPESampler(
                    n_startup_trials=sampler_config.get('n_startup_trials', 5),  # More startup trials for 25 total
                    seed=sampler_config.get('seed', 42)
                ),
                pruner=MedianPruner(
                    n_startup_trials=pruner_config.get('n_startup_trials', 5),  # Wait for 5 trials before pruning
                    n_warmup_steps=pruner_config.get('n_warmup_steps', 3),      # More warmup for stability
                    interval_steps=pruner_config.get('interval_steps', 1)       # Check every trial for pruning
                )
            )
            
            # Run optimization for this layer using the progress utilities
            from skill_similarity_engine.utils.progress import progress_context
            import time
            
            # Use the existing progress utilities with leave=True to keep bars visible
            with progress_context(
                total=trials_per_layer, 
                desc=f"Optimizing {layer_name} ({layer_config['description']}) - {len(layer_jobs)} jobs",
                memory_tracking=False,  # Disable memory tracking for faster updates
                show_tqdm=True
            ) as progress_tracker:
                
                def callback(study, trial):
                    progress_tracker.update(1)
                    # Log pruned trials for transparency
                    if trial.state == optuna.trial.TrialState.PRUNED:
                        print(f"   🔪 Trial {trial.number} pruned early (poor performance)")
                    # Small delay to ensure progress bar visibility for fast layers
                    if len(layer_jobs) < 50:  # For small layers
                        time.sleep(0.05)
                
                study.optimize(
                    lambda trial: self.objective_function_stratified(
                        trial, layer_job_skills, layer_name, layer_config['max_percentile']
                    ),
                    n_trials=trials_per_layer,
                    timeout=timeout_minutes * 60 // len(layers) if len(layers) <= 4 else timeout_minutes * 60 // 4,  # Min 5 min per layer
                    callbacks=[callback]
                )
                
            # Brief pause between layers for visual clarity
            time.sleep(0.2)
            
            # Store results for this layer
            if study.best_trial:
                best_trial = study.best_trial
                # Calculate pruning statistics
                completed_trials = [t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE]
                pruned_trials = [t for t in study.trials if t.state == optuna.trial.TrialState.PRUNED]
                
                stratified_results[layer_name] = {
                    'defining_skills_percentile': best_trial.params['percentile_threshold'],
                    'defining_skills_multiplier': best_trial.params['multiplier'],
                    'job_count': len(layer_jobs),
                    'smoothness_score': best_trial.user_attrs['smoothness_score'],
                    'avg_improvement': best_trial.user_attrs['avg_improvement'],
                    'normalization_factor': best_trial.user_attrs['normalization_factor'],
                    'scores_above_1_percent': best_trial.user_attrs['scores_above_1_percent'],
                    'trial_count': len(study.trials),
                    'completed_trials': len(completed_trials),
                    'pruned_trials': len(pruned_trials),
                    'best_trial': best_trial.number,
                    'max_percentile_cap': layer_config['max_percentile'],
                    'description': f"{layer_config['description']} jobs"
                }
        
        # Calculate global summary
        total_trials = sum(result['trial_count'] for result in stratified_results.values())
        avg_smoothness = np.mean([result['smoothness_score'] for result in stratified_results.values()])
        avg_improvement = np.mean([result['avg_improvement'] for result in stratified_results.values()])
        
        # Print comprehensive summary
        print(f"\n🏆 Stratified Optimization Complete:")
        print(f"   • Total jobs processed: {total_jobs_processed:,}")
        print(f"   • Total trials completed: {total_trials}")
        print(f"   • Layers optimized: {len(stratified_results)}/{len(layers)}")
        if stratified_results:
            print(f"   • Average smoothness: {avg_smoothness:.4f}")
            print(f"   • Average improvement: {avg_improvement*100:.2f}%")
        print()
        
        if stratified_results:
            print("📊 Layer-by-Layer Results:")
            for layer_name, result in stratified_results.items():
                print(f"   {layer_name.replace('_', ' ').title()}:")
                print(f"      Jobs: {result['job_count']:,} | Trials: {result['trial_count']} ({result['completed_trials']} completed, {result['pruned_trials']} pruned)")
                print(f"      Optimal: {result['defining_skills_percentile']:.1f}% percentile, {result['defining_skills_multiplier']:.3f}x multiplier")
                print(f"      Performance: {result['smoothness_score']:.4f} smoothness, {result['avg_improvement']*100:.2f}% improvement")
        else:
            print("⚠️  No layers were successfully optimized.")
            return {}
        
        return {
            'stratified_parameters': stratified_results,
            'global_summary': {
                'total_jobs_processed': total_jobs_processed,
                'total_trials': total_trials,
                'avg_smoothness': avg_smoothness,
                'avg_improvement': avg_improvement
            }
        }


    def run_optimization(self) -> Dict:
        """Run optimization - now defaults to stratified approach"""
        return self.run_stratified_optimization()
    
    def write_yaml_config(self, results: Dict):
        """Write stratified similarity_parameters.yaml"""
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Handle both legacy and stratified results
        if 'stratified_parameters' in results:
            # Stratified results
            stratified_params = results['stratified_parameters']
            global_summary = results['global_summary']
            
            # Use first layer's parameters as global fallback
            first_layer = next(iter(stratified_params.values()))
            fallback_percentile = first_layer['defining_skills_percentile']
            fallback_multiplier = first_layer['defining_skills_multiplier']
            
            yaml_content = f"""# =============================================================================
# Core - Similarity Parameters Configuration
# =============================================================================
# 
# CRITICAL PARAMETERS - These values are the result of Stratified Optuna Bayesian optimization
# and are fundamental to the career pathway intelligence algorithms.
# 
# AUTO-GENERATED on {current_date} - DO NOT MODIFY manually
# =============================================================================

# Optuna-Optimized Parameters ({current_date})
# Based on stratified dataset optimization with asymmetric Jaccard + corpus normalization
# NOTE: This file is loaded as core.similarity_parameters by the config manager
optuna_optimal:
  # Global fallback parameters (for backward compatibility)
  defining_skills_percentile: {fallback_percentile:.1f}
  defining_skills_multiplier: {fallback_multiplier:.3f}
  
  # Stratified optimization results (job size specific parameters)
  stratified_parameters:"""
            
            # Add each layer's parameters
            for layer_name, layer_data in stratified_params.items():
                yaml_content += f"""
    {layer_name}:
      defining_skills_percentile: {layer_data['defining_skills_percentile']:.1f}
      defining_skills_multiplier: {layer_data['defining_skills_multiplier']:.3f}
      job_count: {layer_data['job_count']}
      smoothness_score: {layer_data['smoothness_score']:.4f}
      avg_improvement: {layer_data['avg_improvement']:.4f}
      normalization_factor: {layer_data['normalization_factor']:.4f}
      scores_above_1_percent: {layer_data['scores_above_1_percent']:.2f}
      trial_count: {layer_data['trial_count']}
      best_trial: {layer_data['best_trial']}
      max_percentile_cap: {layer_data['max_percentile_cap']:.1f}
      description: "{layer_data['description']}\""""
            
            yaml_content += f"""
  
  # Global optimization metadata
  optimization_metadata:
    optimization_date: "{current_date}"
    optimization_method: "Stratified Optuna TPE Sampler + Median Pruner"
    dataset_size: "Stratified by job size with business constraints"
    objective_function: "Layer-specific smoothness optimization with improvement penalty"
    total_jobs_processed: {global_summary['total_jobs_processed']}
    total_trials: {global_summary['total_trials']}
    avg_smoothness: {global_summary['avg_smoothness']:.4f}
    avg_improvement: {global_summary['avg_improvement']:.4f}
    stratification_strategy: "4 layers by skill count with percentile caps"

# Rarity Analysis Parameters
rarity_thresholds:
  rare_threshold: 5.0          # Skills in <5% of jobs = rare
  uncommon_threshold: 20.0     # Skills in 5-20% of jobs = uncommon
  common_threshold: 50.0       # Skills in 20-50% of jobs = common

# Similarity Calculation Method
similarity_method:
  algorithm: "asymmetric_jaccard"
  description: "Asymmetric Jaccard measures transition readiness (|A ∩ B| / |A|)"
  
  corpus_normalization:
    enabled: true
    method: "max_normalization"
    preserve_differentiation: true
    allow_intermediate_scores_above_1: true

# Algorithm Configuration
algorithm_config:
  calculation_steps:
    1: "Calculate asymmetric Jaccard baseline (|shared| / |job_a_skills|)"
    2: "Identify defining skills using stratified parameters per job size"
    3: "Find shared defining skills between jobs"
    4: "Apply layer-specific multiplier boost for shared defining skills"
    5: "Allow scores >1.0 for corpus normalization"
    6: "Normalize entire corpus to 0-1 range preserving differentiation"
  
  store_both_raw_and_normalized: true
  primary_score_field: "similarity_score"
  raw_score_field: "raw_similarity_score"

# Business Logic Constraints (Override Optimization Results)
business_constraints:
  # Dynamic defining skills limits based on job size
  defining_skills_limits:
    enabled: true
    
    # Job size categories and their constraints
    job_size_categories:
      small:
        max_skills_threshold: 15
        max_percentile_cap: 50.0
        description: "Small jobs (≤15 skills): max 50% percentile → 3-7 defining skills"
      medium:
        max_skills_threshold: 30
        max_percentile_cap: 30.0
        description: "Medium jobs (16-30 skills): max 30% percentile → 5-9 defining skills"
      large:
        max_skills_threshold: 50
        max_percentile_cap: 20.0
        description: "Large jobs (31-50 skills): max 20% percentile → 6-10 defining skills"
      xlarge:
        max_skills_threshold: 999
        max_percentile_cap: 15.0
        description: "XLarge jobs (>50 skills): max 15% percentile → 8-15 defining skills"
    
    # Absolute business limits (hard caps)
    absolute_limits:
      max_defining_skills_per_job: 10
      min_defining_skills_per_job: 1
    
    # Constraint application behavior
    override_optimization: true
    log_constraint_applications: true
    constraint_priority: "business_first"  # business_first, optimization_first

# Enhanced Similarity Normalization Rules
normalization_config:
  # Column-specific normalization
  normalize_enhanced_similarity_score: true
  preserve_raw_rarity_weighted_score: true
  
  # Database column mapping
  primary_normalized_column: "enhanced_similarity_score"
  raw_values_column: "rarity_weighted_score"
  
  # Normalization behavior
  method: "corpus_max_normalization"
  preserve_score_differentiation: true
  allow_intermediate_scores_above_1: true

# Validation and Quality Assurance
validation:
  expected_performance:
    smoothness_score_min: 0.70
    average_improvement_min: 0.005
    normalization_factor_range: [1.0, 5.0]
    scores_above_1_percent_max: 60.0
  
  quality_checks:
    validate_asymmetric_calculation: true
    verify_defining_skills_logic: true
    check_corpus_normalization: true
    ensure_0_1_final_range: true

# Configuration Metadata
metadata:
  version: "3.2"
  last_updated: "{current_date}"
  optimization_source: "Stratified Optuna Bayesian Optimization with Business Constraints"
  critical_for_modules:
    - "similarity/defining_skills.py"
    - "similarity/rarity_weighted.py" 
    - "similarity/asymmetric.py"
    - "business_context/analytics_orchestrator.py"
  description: "Auto-generated stratified optimal similarity parameters with business logic constraints"
"""
        else:
            # Legacy single optimization results (minimal fallback)
            yaml_content = f"""# Legacy optimization result - consider running stratified optimization
optuna_optimal:
  defining_skills_percentile: {results.get('percentile_threshold', 49.9):.1f}
  defining_skills_multiplier: {results.get('multiplier', 1.5):.3f}
"""
        
        # Write the file
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            f.write(yaml_content)
        
        print(f"✅ Configuration written to: {self.config_path}")
    
    def optimize_and_update(self) -> bool:
        """Run complete optimization and update config"""
        try:
            results = self.run_optimization()
            
            # Check if optimization was cancelled or failed
            if not results:
                print("⚠️  Optimization was cancelled or failed.")
                return False
            
            # Validate stratified results format
            if 'stratified_parameters' in results:
                # Stratified results validation
                stratified_params = results['stratified_parameters']
                if not stratified_params:
                    print("❌ No stratified parameters found in optimization results.")
                    return False
                
                # Validate each layer has required data
                for layer_name, layer_data in stratified_params.items():
                    required_layer_keys = ['defining_skills_percentile', 'defining_skills_multiplier', 'job_count']
                    missing_layer_keys = [key for key in required_layer_keys if key not in layer_data]
                    if missing_layer_keys:
                        print(f"❌ Layer {layer_name} missing required data: {missing_layer_keys}")
                        return False
                
                print(f"✅ Stratified optimization validated successfully!")
                print(f"   • {len(stratified_params)} job size layers optimized")
                print(f"   • {results['global_summary']['total_jobs_processed']} jobs processed")
            else:
                # Legacy results validation
                required_keys = ['percentile_threshold', 'multiplier', 'trial_count', 'best_trial']
                missing_keys = [key for key in required_keys if key not in results]
                if missing_keys:
                    print(f"❌ Optimization results missing required data: {missing_keys}")
                    return False
            
            self.write_yaml_config(results)
            print(f"🎉 Optimization complete! Enhanced Similarity Analytics will use new parameters.")
            return True
        except Exception as e:
            print(f"❌ Optimization failed: {e}")
            return False
    
    @staticmethod
    def is_available() -> bool:
        """Check if optimization is available"""
        return OPTUNA_AVAILABLE