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
        
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        
        if not OPTUNA_AVAILABLE:
            raise ImportError("Optuna not available. Install with: pip install optuna")
    
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
        percentile_threshold = trial.suggest_float('percentile_threshold', 5, 50)
        multiplier = trial.suggest_float('multiplier', 1.01, 1.50)
        
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
    
    def calculate_stratified_sample_size(self, strata_info: list, confidence_level: float = 0.95, margin_of_error: float = 0.05) -> int:
        """Calculate optimal sample size using stratified sampling theory"""
        import math
        
        if not strata_info:
            return 12  # Minimum fallback
            
        # Z-score for confidence level
        z_scores = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}
        z = z_scores.get(confidence_level, 1.96)
        
        # Calculate total population and weighted variance
        total_population = sum(stratum['size'] for stratum in strata_info)
        
        # Neyman allocation formula components
        numerator_sum = sum(stratum['size'] * math.sqrt(stratum['variance']) for stratum in strata_info)
        denominator_sum = sum(stratum['size'] * stratum['variance'] for stratum in strata_info)
        
        # Sample size calculation
        if denominator_sum == 0:
            return 12
            
        sample_size = (z**2 * numerator_sum**2) / (
            (margin_of_error**2 * total_population**2) + (z**2 * denominator_sum)
        )
        
        # Apply practical bounds
        return max(8, min(60, int(sample_size)))

    def calculate_stratified_trials(self, jobs_df: pd.DataFrame, job_skills_df: pd.DataFrame) -> int:
        """Calculate optimal trials based on job-skill diversity stratification"""
        print("📊 Analyzing corpus diversity for optimal trial calculation...")
        
        # Create job skill profiles
        print("   • Building job skill profiles...")
        job_skill_sets = {}
        for _, row in job_skills_df.iterrows():
            job_id = row['JobProfileID']
            skill = row['Skill_Name']
            if job_id not in job_skill_sets:
                job_skill_sets[job_id] = set()
            job_skill_sets[job_id].add(skill)
        
        # Calculate skill rarity
        print("   • Calculating skill rarity distribution...")
        skill_counts = job_skills_df['Skill_Name'].value_counts()
        total_jobs = len(jobs_df)
        skill_rarity = {skill: count/total_jobs for skill, count in skill_counts.items()}
        
        # Stratify jobs by skill diversity characteristics
        print("   • Stratifying jobs by skill diversity patterns...")
        job_characteristics = []
        
        for job_id, skills in job_skill_sets.items():
            if not skills:
                continue
                
            # Calculate job characteristics
            skill_count = len(skills)
            avg_rarity = sum(skill_rarity[skill] for skill in skills) / len(skills)
            rare_skills_pct = sum(1 for skill in skills if skill_rarity[skill] < 0.1) / len(skills)
            
            job_characteristics.append({
                'job_id': job_id,
                'skill_count': skill_count,
                'avg_rarity': avg_rarity,
                'rare_skills_pct': rare_skills_pct
            })
        
        # Create strata based on skill patterns
        print("   • Creating representative strata...")
        strata = self._create_job_strata(job_characteristics)
        
        # Calculate optimal sample size
        print("   • Calculating optimal sample size using stratified sampling theory...")
        optimal_trials = self.calculate_stratified_sample_size(strata)
        
        # Display stratification results
        print(f"📊 Stratified Sampling Analysis:")
        print(f"   • Total jobs analyzed: {len(job_characteristics):,}")
        print(f"   • Number of strata: {len(strata)}")
        for i, stratum in enumerate(strata, 1):
            print(f"   • Stratum {i}: {stratum['size']} jobs ({stratum['description']})")
        print(f"   • Optimal trials: {optimal_trials}")
        print(f"   • Confidence level: 95%, Margin of error: 5%")
        
        return optimal_trials

    def _create_job_strata(self, job_characteristics: list) -> list:
        """Create strata based on job skill diversity patterns"""
        import numpy as np
        
        if not job_characteristics:
            return []
        
        # Extract characteristics for stratification
        skill_counts = [job['skill_count'] for job in job_characteristics]
        avg_rarities = [job['avg_rarity'] for job in job_characteristics]
        rare_pcts = [job['rare_skills_pct'] for job in job_characteristics]
        
        # Define strata based on skill patterns
        strata = []
        
        # Stratum 1: Small skill sets with common skills
        small_common = [job for job in job_characteristics 
                       if job['skill_count'] <= 30 and job['rare_skills_pct'] < 0.3]
        if small_common:
            strata.append({
                'size': len(small_common),
                'variance': np.var([job['avg_rarity'] for job in small_common]) if len(small_common) > 1 else 0.1,
                'description': 'Small jobs, common skills'
            })
        
        # Stratum 2: Medium skill sets with balanced rarity
        medium_balanced = [job for job in job_characteristics 
                          if 30 < job['skill_count'] <= 60 and 0.3 <= job['rare_skills_pct'] < 0.7]
        if medium_balanced:
            strata.append({
                'size': len(medium_balanced),
                'variance': np.var([job['avg_rarity'] for job in medium_balanced]) if len(medium_balanced) > 1 else 0.15,
                'description': 'Medium jobs, balanced skills'
            })
        
        # Stratum 3: Large skill sets with rare skills
        large_rare = [job for job in job_characteristics 
                     if job['skill_count'] > 60 or job['rare_skills_pct'] >= 0.7]
        if large_rare:
            strata.append({
                'size': len(large_rare),
                'variance': np.var([job['avg_rarity'] for job in large_rare]) if len(large_rare) > 1 else 0.2,
                'description': 'Large/rare-heavy jobs'
            })
        
        # Stratum 4: Edge cases (very small or very specific patterns)
        edge_cases = [job for job in job_characteristics 
                     if job['skill_count'] <= 10 or job['rare_skills_pct'] >= 0.9]
        if edge_cases and len(edge_cases) > 2:  # Only if significant
            strata.append({
                'size': len(edge_cases),
                'variance': 0.25,  # High variance for edge cases
                'description': 'Edge cases (very small/specialized)'
            })
        
        # Ensure we have at least one stratum
        if not strata:
            strata.append({
                'size': len(job_characteristics),
                'variance': np.var(avg_rarities) if len(avg_rarities) > 1 else 0.1,
                'description': 'All jobs (single stratum)'
            })
        
        return strata

    def create_early_stopping_callback(self, convergence_window: int = 8, improvement_threshold: float = 0.02):
        """Create callback for early stopping based on convergence and diminishing returns"""
        def callback(study, trial):
            trials = study.trials
            n_trials = len(trials)
            
            # Need minimum trials for meaningful analysis
            if n_trials < convergence_window:
                return
                
            # Get valid trial values
            valid_trials = [t for t in trials if t.value is not None]
            if len(valid_trials) < convergence_window:
                return
                
            # Check convergence: no improvement in recent window
            recent_values = [t.value for t in valid_trials[-convergence_window:]]
            best_recent = min(recent_values)
            best_overall = study.best_value
            
            if abs(best_recent - best_overall) < improvement_threshold:
                print(f"\n🎯 Early stopping: No improvement >2% in last {convergence_window} trials")
                study.stop()
                return
                
            # Check diminishing returns: last 5 trials show minimal improvement
            if n_trials >= 12:  # Need enough data for trend analysis
                recent_5_values = [t.value for t in valid_trials[-5:]]
                previous_best = min([t.value for t in valid_trials[:-5]])
                current_best = min(recent_5_values)
                
                improvement_rate = abs(current_best - previous_best) / abs(previous_best) if previous_best != 0 else 0
                
                if improvement_rate < 0.01:  # Less than 1% improvement
                    print(f"\n🎯 Early stopping: Diminishing returns detected (<1% improvement in last 5 trials)")
                    study.stop()
                    return
                
        return callback

    def run_optimization(self) -> Dict:
        """Run optimization with adaptive trials and early stopping"""
        print("🚀 Starting Optuna optimization...")
        
        jobs_df, job_skills_df = self.load_data()
        num_jobs = len(jobs_df)
        num_skills = job_skills_df['Skill_Name'].nunique()
        print(f"✅ Loaded {num_jobs} jobs and {len(job_skills_df):,} job-skill relationships")
        
        # Calculate optimal trials using stratified sampling
        recommended_trials = self.calculate_stratified_trials(jobs_df, job_skills_df)
        
        # Ask user for trial count with smart default
        print(f"\n🎯 Trial Selection:")
        print(f"   Recommended trials: {recommended_trials} (based on stratified sampling)")
        print(f"   You can accept this recommendation or specify a different number.")
        print(f"   Note: Early stopping will still apply regardless of your choice.")
        
        trial_input = input(f"   How many trials would you like to run? (default: {recommended_trials}): ").strip()
        
        if trial_input == "":
            max_trials = recommended_trials
            print(f"   ✅ Using recommended trials: {recommended_trials}")
        else:
            try:
                user_trials = int(trial_input)
                if user_trials < 1:
                    print(f"   ❌ Invalid number. Using recommended: {recommended_trials}")
                    max_trials = recommended_trials
                elif user_trials > 200:
                    print(f"   ⚠️  Very high trial count! This could take hours.")
                    confirm = input(f"   Continue with {user_trials} trials? (y/N): ").strip().lower()
                    if confirm == 'y':
                        max_trials = user_trials
                        print(f"   ✅ Using custom trials: {user_trials}")
                    else:
                        max_trials = recommended_trials
                        print(f"   ✅ Using recommended trials: {recommended_trials}")
                else:
                    max_trials = user_trials
                    print(f"   ✅ Using custom trials: {user_trials}")
            except ValueError:
                print(f"   ❌ Invalid input. Using recommended: {recommended_trials}")
                max_trials = recommended_trials
        
        study = optuna.create_study(
            direction='minimize',
            sampler=TPESampler(n_startup_trials=5, seed=42),
            pruner=MedianPruner(n_startup_trials=5, n_warmup_steps=3)
        )
        
        # Create early stopping callback
        early_stopping = self.create_early_stopping_callback()
        
        print(f"\n🎯 Final Optimization Strategy:")
        print(f"   • Maximum trials: {max_trials}")
        print(f"   • Convergence stopping: No improvement >2% in 8 trials")
        print(f"   • Diminishing returns: <1% improvement in last 5 trials")
        print(f"   • Time safety net: 20 minutes maximum")
        if max_trials != recommended_trials:
            print(f"   • Note: Using {max_trials} instead of recommended {recommended_trials}")
        print()
        
        # Run optimization with adaptive parameters
        study.optimize(
            lambda trial: self.objective_function(trial, jobs_df, job_skills_df),
            n_trials=max_trials,
            timeout=1200,  # 20 minutes max
            callbacks=[early_stopping],
            show_progress_bar=True
        )
        
        # Get best results and stopping reason
        best_trial = study.best_trial
        total_trials_run = len(study.trials)
        
        print(f"\n🏆 Optimization Complete:")
        print(f"   • Trials completed: {total_trials_run}/{max_trials}")
        if total_trials_run < max_trials:
            print(f"   • Stopped early: Convergence detected")
        else:
            print(f"   • Stopped: Maximum trials reached")
        
        print(f"\n📊 Best trial: {best_trial.number}")
        print(f"📊 Best parameters:")
        print(f"   • Percentile threshold: {best_trial.params['percentile_threshold']:.1f}%")
        print(f"   • Multiplier: {best_trial.params['multiplier']:.3f}x")
        print(f"   • Smoothness score: {best_trial.user_attrs['smoothness_score']:.4f}")
        print(f"   • Average improvement: {best_trial.user_attrs['avg_improvement']*100:.2f}%")
        
        # Ask user which trial to use
        print(f"\n🎯 Trial Selection:")
        print(f"   The systematically determined best trial is {best_trial.number}")
        print(f"   You can accept this, or specify a different trial number (0-{len(study.trials)-1})")
        
        trial_choice = input(f"   Which trial would you like to use? (default: {best_trial.number}): ").strip()
        
        if trial_choice == "":
            selected_trial = best_trial
            print(f"   ✅ Using best trial: {best_trial.number}")
        else:
            try:
                trial_num = int(trial_choice)
                if 0 <= trial_num < len(study.trials):
                    selected_trial = study.trials[trial_num]
                    print(f"   ✅ Using selected trial: {trial_num}")
                    print(f"   📊 Selected parameters:")
                    print(f"      • Percentile threshold: {selected_trial.params['percentile_threshold']:.1f}%")
                    print(f"      • Multiplier: {selected_trial.params['multiplier']:.3f}x")
                    print(f"      • Smoothness score: {selected_trial.user_attrs['smoothness_score']:.4f}")
                    print(f"      • Average improvement: {selected_trial.user_attrs['avg_improvement']*100:.2f}%")
                else:
                    print(f"   ❌ Invalid trial number. Using best trial: {best_trial.number}")
                    selected_trial = best_trial
            except ValueError:
                print(f"   ❌ Invalid input. Using best trial: {best_trial.number}")
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