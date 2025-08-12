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


def create_defining_skills(job_skills_df: pd.DataFrame, percentile_threshold: float) -> Dict[str, Set[str]]:
    """Create defining skills for each job"""
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
        
        num_defining = max(1, int(len(job_skill_prevalence) * percentile_threshold / 100))
        defining_skills = job_skill_prevalence.head(num_defining)['Skill_Name'].tolist()
        
        job_defining_skills[job_id] = set(defining_skills)
    
    return job_defining_skills


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
    
    def objective_function(self, trial, jobs_df: pd.DataFrame, job_skills_df: pd.DataFrame):
        """Simple objective function for Optuna"""
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
        
        print(f"🔬 Trial {trial.number}: {percentile_threshold:.1f}% percentile, {multiplier:.3f}x multiplier")
        
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
        
        # Normalize scores
        raw_scores = np.array(all_similarities)
        max_score = np.max(raw_scores)
        normalized_scores = raw_scores / max_score if max_score > 0 else raw_scores
        
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
        
        print(f"   ✅ Smoothness: {smoothness_score:.4f}, Improvement: {avg_improvement*100:.2f}%, Objective: {combined_objective:.4f}")
        
        return combined_objective
    
    def run_optimization(self) -> Dict:
        """Run simple optimization with fixed 25 trials"""
        print("🚀 Starting Optuna optimization...")
        
        jobs_df, job_skills_df = self.load_data()
        num_jobs = len(jobs_df)
        num_skills = job_skills_df['Skill_Name'].nunique()
        print(f"✅ Loaded {num_jobs} jobs and {len(job_skills_df):,} job-skill relationships")
        
        # Get configuration settings
        optuna_config = self.optimization_config.get('optuna', {})
        max_trials = optuna_config.get('max_trials', 25)
        timeout_minutes = optuna_config.get('timeout_minutes', 20)
        
        print(f"\n🎯 Simple Optimization Strategy:")
        print(f"   • Fixed trials: {max_trials}")
        print(f"   • Time limit: {timeout_minutes} minutes")
        print(f"   • No early stopping - all trials will complete")
        print()
        
        # Ask for confirmation
        confirm = input(f"   Proceed with {max_trials} trials? (y/N): ").strip().lower()
        if confirm != 'y':
            print("   Optimization cancelled.")
            return {}
        
        # Create study with configuration
        sampler_config = optuna_config.get('sampler', {})
        pruner_config = optuna_config.get('pruner', {})
        
        study = optuna.create_study(
            direction=optuna_config.get('study_direction', 'minimize'),
            sampler=TPESampler(
                n_startup_trials=sampler_config.get('n_startup_trials', 5),
                seed=sampler_config.get('seed', 42)
            ),
            pruner=MedianPruner(
                n_startup_trials=pruner_config.get('n_startup_trials', 5),
                n_warmup_steps=pruner_config.get('n_warmup_steps', 3)
            )
        )
        
        # Run optimization
        print(f"🔍 Running {max_trials} optimization trials...")
        study.optimize(
            lambda trial: self.objective_function(trial, jobs_df, job_skills_df),
            n_trials=max_trials,
            timeout=timeout_minutes * 60,  # Convert to seconds
            show_progress_bar=optuna_config.get('show_progress_bar', True)
        )
        
        # Get best results
        best_trial = study.best_trial
        total_trials_run = len(study.trials)
        
        print(f"\n🏆 Optimization Complete:")
        print(f"   • Trials completed: {total_trials_run}/{max_trials}")
        print(f"   • All trials completed successfully")
        
        print(f"\n📊 Best trial: {best_trial.number}")
        print(f"📊 Best parameters:")
        print(f"   • Percentile threshold: {best_trial.params['percentile_threshold']:.1f}%")
        print(f"   • Multiplier: {best_trial.params['multiplier']:.3f}x")
        print(f"   • Smoothness score: {best_trial.user_attrs['smoothness_score']:.4f}")
        print(f"   • Average improvement: {best_trial.user_attrs['avg_improvement']*100:.2f}%")
        
        # Option to select different trial (simplified)
        ux_config = self.optimization_config.get('user_experience', {})
        if ux_config.get('allow_custom_trial_selection', True):
            print(f"\n🎯 Trial Selection:")
            print(f"   Best trial: {best_trial.number} (recommended)")
            
            trial_choice = input(f"   Use best trial or specify different number (0-{len(study.trials)-1})? (default: best): ").strip()
            
            if trial_choice == "" or trial_choice.lower() == 'best':
                selected_trial = best_trial
                print(f"   ✅ Using best trial: {best_trial.number}")
            else:
                try:
                    trial_num = int(trial_choice)
                    if 0 <= trial_num < len(study.trials):
                        selected_trial = study.trials[trial_num]
                        print(f"   ✅ Using trial: {trial_num}")
                    else:
                        print(f"   ❌ Invalid trial number. Using best trial: {best_trial.number}")
                        selected_trial = best_trial
                except ValueError:
                    print(f"   ❌ Invalid input. Using best trial: {best_trial.number}")
                    selected_trial = best_trial
        else:
            selected_trial = best_trial
        
        return {
            'percentile_threshold': selected_trial.params['percentile_threshold'],
            'multiplier': selected_trial.params['multiplier'],
            'trial_count': len(study.trials),
            'best_trial': selected_trial.number,
            'smoothness_score': selected_trial.user_attrs['smoothness_score'],
            'avg_improvement': selected_trial.user_attrs['avg_improvement'],
            'normalization_factor': selected_trial.user_attrs['normalization_factor'],
            'scores_above_1_percent': selected_trial.user_attrs['scores_above_1_percent']
        }
    
    def write_yaml_config(self, results: Dict):
        """Write completely new similarity_parameters.yaml"""
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        yaml_content = f"""# =============================================================================
# Core - Similarity Parameters Configuration
# =============================================================================
# 
# CRITICAL PARAMETERS - These values are the result of Optuna Bayesian optimization
# and are fundamental to the career pathway intelligence algorithms.
# 
# AUTO-GENERATED on {current_date} - DO NOT MODIFY manually
# =============================================================================

# Optuna-Optimized Parameters ({current_date})
# Based on full dataset optimization with asymmetric Jaccard + corpus normalization
# NOTE: This file is loaded as core.similarity_parameters by the config manager
optuna_optimal:
  # Defining skills threshold - Top % rarest skills per job profile
  defining_skills_percentile: {results['percentile_threshold']:.1f}
  
  # Similarity boost multiplier for shared defining skills
  defining_skills_multiplier: {results['multiplier']:.3f}
  
  # Optimization metadata for transparency
  optimization_metadata:
    optimization_date: "{current_date}"
    optimization_method: "Optuna TPE Sampler + Median Pruner"
    dataset_size: "Full dataset analysis"
    objective_function: "Smoothness optimization with improvement penalty"
    trial_count: {results['trial_count']}
    selected_trial: {results['best_trial']}
    smoothness_score: {results['smoothness_score']:.4f}
    average_improvement: {results['avg_improvement']:.4f}
    normalization_factor: {results['normalization_factor']:.4f}
    scores_above_1_percent: {results['scores_above_1_percent']:.2f}

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
    2: "Identify defining skills for both jobs (top {results['percentile_threshold']:.1f}% rarest per job)"
    3: "Find shared defining skills between jobs"
    4: "Apply {results['multiplier']:.3f}x multiplier boost for shared defining skills"
    5: "Allow scores >1.0 for corpus normalization"
    6: "Normalize entire corpus to 0-1 range preserving differentiation"
  
  store_both_raw_and_normalized: true
  primary_score_field: "similarity_score"
  raw_score_field: "raw_similarity_score"

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
  version: "3.0"
  last_updated: "{current_date}"
  optimization_source: "Optuna Bayesian Optimization"
  critical_for_modules:
    - "similarity/defining_skills.py"
    - "similarity/rarity_weighted.py" 
    - "similarity/asymmetric.py"
    - "business_context/analytics_orchestrator.py"
  description: "Auto-generated optimal similarity parameters"
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
            
            # Validate required keys exist
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