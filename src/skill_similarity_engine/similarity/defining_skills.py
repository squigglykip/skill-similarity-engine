"""
Defining Skills Analysis Module

Handles identification and analysis of job-specific defining skills using empirically-tuned
percentile thresholds. Defining skills are the top 20% rarest skills per job profile that
characterize specific role archetypes and provide career pathway intelligence.

Based on hyperparameter tuning results:
- 20% percentile threshold for defining skills identification
- Optimized for 0.76% average improvement and 12.5% positive impact rate
- 0.7714 smoothness score (optimal balance of smoothness + practical impact)
"""

import logging
import sqlite3
import pandas as pd
from typing import Dict, Set, Any, List, Optional
from ..utils.progress import progress_context
from ..config.architectural_config_manager import get_config_manager

# Load configuration manager for externalized parameters
_config_manager = get_config_manager()

# Load Optuna-optimized parameters from core configuration
_similarity_params = _config_manager.get_nested_value(
    'core', 'similarity_parameters', 'optuna_optimal'
)

if not _similarity_params:
    raise ValueError(
        "Missing required configuration: core.similarity_parameters.optuna_optimal. "
        "Please ensure config/core/similarity_parameters.yaml contains the required parameters."
    )

# Configuration constants (loaded from config/core/similarity_parameters.yaml)
DEFINING_SKILLS_PERCENTILE = _similarity_params['defining_skills_percentile']


class DefiningSkillsAnalyzer:
    """
    Analyzes and identifies job-specific defining skills.
    
    This class creates job-specific defining skills mappings using empirically-tuned
    percentile thresholds that optimize career pathway intelligence.
    """
    
    def __init__(self, 
                 defining_skills_percentile: float = DEFINING_SKILLS_PERCENTILE):
        """
        Initialize the defining skills analyzer.
        
        Args:
            defining_skills_percentile: Top % rarest skills per job (default: 8.8)
        """
        self.defining_skills_percentile = defining_skills_percentile
        self.logger = logging.getLogger(__name__)
        
    def create_job_specific_defining_skills(self, 
                                          skill_universe: pd.DataFrame, 
                                          job_skills_df: pd.DataFrame) -> Dict[str, Set[str]]:
        """
        Create job-specific defining skills using empirically-tuned percentile threshold with business constraints.
        
        Uses top X% rarest skills per job profile based on Optuna optimization results with business logic:
        - Dynamic percentile scaling based on job size for realistic defining skills counts
        - Business constraints override optimization when needed for practical application
        
        Args:
            skill_universe: DataFrame with all skills and their global rarity/prevalence
            job_skills_df: DataFrame with job-skill relationships
            
        Returns:
            Dict mapping JobProfileID to Set of defining skill names for that job
        """
        # Load configuration metadata for display
        from ..config.architectural_config_manager import get_config_manager
        config_manager = get_config_manager()
        optimization_metadata = config_manager.get_nested_value(
            'core', 'similarity_parameters', 'optuna_optimal', 'optimization_metadata'
        )
        
        # Load business constraints
        business_constraints = config_manager.get_nested_value(
            'core', 'similarity_parameters', 'business_constraints'
        )
        
        print(f"🎯 Creating job-specific defining skills with business constraints")
        if optimization_metadata:
            # Check for stratified optimization metadata
            if 'stratification_strategy' in optimization_metadata:
                # Stratified optimization
                avg_improvement = optimization_metadata.get('avg_improvement', 0) * 100  # Convert to percentage
                smoothness_score = optimization_metadata.get('avg_smoothness', 0)
                total_trials = optimization_metadata.get('total_trials', 0)
                total_jobs = optimization_metadata.get('total_jobs_processed', 0)
                print(f"   Based on Stratified Optuna optimization: {avg_improvement:.2f}% avg improvement, enhanced differentiation")
                print(f"   Smoothness score: {smoothness_score:.4f} (optimal balance across {total_trials} trials, {total_jobs} jobs)")
            else:
                # Legacy optimization
                avg_improvement = optimization_metadata.get('average_improvement', 0) * 100  # Convert to percentage
                smoothness_score = optimization_metadata.get('smoothness_score', 0)
                print(f"   Based on Optuna optimization: {avg_improvement:.2f}% avg improvement, enhanced differentiation")
                print(f"   Smoothness score: {smoothness_score:.4f} (optimal balance of smoothness + practical impact)")
        
        if business_constraints and business_constraints.get('defining_skills_limits', {}).get('enabled', False):
            print(f"   🏢 Business constraints enabled: Dynamic scaling by job size")
        else:
            print(f"   Using base percentile: {self.defining_skills_percentile}% rarest per role")
        
        job_defining_skills = {}
        
        # Group by JobProfileID to get skills per job
        job_groups = list(job_skills_df.groupby('JobProfileID'))
        
        with progress_context(
            total=len(job_groups),
            desc="Defining Skills Analysis",
            memory_tracking=True,
            show_tqdm=True
        ) as progress:
            
            for job_id, job_group in job_groups:
                job_skill_names = job_group['Skill_Name'].tolist()
                
                # Get rarity info for this job's skills from skill_universe
                job_skills_with_rarity = skill_universe[
                    skill_universe['Skill_Name'].isin(job_skill_names)
                ].copy()
                
                # Sort by prevalence (ascending = rarest first), then by skill name for deterministic tie-breaking
                job_skills_with_rarity = job_skills_with_rarity.sort_values(['prevalence_percentage', 'Skill_Name'])
                
                job_skill_count = len(job_skills_with_rarity)
                
                # Try to get stratified parameters first, then apply business constraints as fallback
                effective_percentile, effective_multiplier = self._get_optimal_parameters_for_job(job_skill_count)
                
                # Apply business constraints as a secondary safeguard (if stratified parameters aren't available)
                if business_constraints and business_constraints.get('defining_skills_limits', {}).get('enabled', False):
                    effective_percentile = self._apply_business_constraints(
                        job_skill_count, effective_percentile, business_constraints
                    )
                
                # Calculate number of defining skills with effective percentile
                num_defining = max(1, int(len(job_skills_with_rarity) * effective_percentile / 100))
                
                # Apply absolute business limits if configured
                if business_constraints and business_constraints.get('defining_skills_limits', {}).get('enabled', False):
                    absolute_limits = business_constraints.get('defining_skills_limits', {}).get('absolute_limits', {})
                    max_defining = absolute_limits.get('max_defining_skills_per_job', num_defining)
                    min_defining = absolute_limits.get('min_defining_skills_per_job', 1)
                    num_defining = max(min_defining, min(num_defining, max_defining))
                
                defining_for_this_job = job_skills_with_rarity.head(num_defining)['Skill_Name'].tolist()
                
                job_defining_skills[job_id] = set(defining_for_this_job)
                progress.update(1)
        
        # Calculate summary statistics
        total_jobs = len(job_defining_skills)
        total_defining_relationships = sum(len(skills) for skills in job_defining_skills.values())
        avg_defining_per_job = total_defining_relationships / total_jobs if total_jobs > 0 else 0
        
        print(f"   ✅ Created defining skills for {total_jobs:,} jobs")
        print(f"   📊 {total_defining_relationships:,} defining skills • {avg_defining_per_job:.1f} per job average")
        
        return job_defining_skills
    
    def generate_job_defining_skills_analysis(self, 
                                            job_defining_skills: Dict[str, Set[str]],
                                            skill_universe: pd.DataFrame,
                                            job_skills_df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate comprehensive job defining skills analysis for database population.
        
        Args:
            job_defining_skills: Dict mapping job ID to set of defining skill names
            skill_universe: DataFrame with skill prevalence data
            job_skills_df: DataFrame with job-skill relationships
            
        Returns:
            DataFrame formatted for analytics_job_defining_skills table
        """
        # Starting job defining skills analysis generation
        
        defining_records = []
        total_records = sum(len(skills) for skills in job_defining_skills.values())
        
        with progress_context(
            total=total_records,
            desc="Job Defining Skills Analysis",
            memory_tracking=True,
            show_tqdm=True
        ) as progress:
            
            for job_id, defining_skills in job_defining_skills.items():
                # Get job info
                job_info = job_skills_df[job_skills_df['JobProfileID'] == job_id].iloc[0]
                
                for skill_name in defining_skills:
                    # Get skill details from skill universe
                    skill_info = skill_universe[skill_universe['Skill_Name'] == skill_name]
                    
                    if not skill_info.empty:
                        skill_row = skill_info.iloc[0]
                        
                        defining_record = {
                            'job_profile_id': job_id,
                            'skill_id': skill_row['Skill_ID'],
                            'skill_name': skill_name,
                            'job_profile': job_info['JobProfile'],
                            'category': skill_row['Category'],
                            'subcategory': skill_row.get('Subcategory', ''),
                            'skill_type': skill_row['SkillType'],
                            'prevalence_percentage': round(skill_row['prevalence_percentage'], 2),
                            'total_profiles_with_skill': int(skill_row['job_profiles_with_skill']),
                            'rarity_category': skill_row['rarity_category'],
                            'defining_skill_rank': self._get_defining_rank(
                                job_id, skill_name, job_defining_skills, skill_universe
                            ),
                            'defining_skill_score': 100.0 - skill_row['prevalence_percentage'],  # Inverse of prevalence
                            'analysis_date': pd.Timestamp.now().strftime('%Y-%m-%d'),
                            'percentile_threshold': 8.8  # Top 8.8% rarest skills (Optuna optimal)
                        }
                        
                        defining_records.append(defining_record)
                    
                    progress.update(1)
        
        defining_df = pd.DataFrame(defining_records)
        
        print(f"   ✅ Generated defining skills analysis for {len(defining_df):,} job-skill pairs")
        
        # Show summary statistics
        unique_jobs = defining_df['job_profile_id'].nunique()
        unique_skills = defining_df['skill_id'].nunique()
        avg_defining_per_job = len(defining_df) / unique_jobs if unique_jobs > 0 else 0
        
        print(f"   📊 {unique_jobs:,} jobs • {unique_skills:,} defining skills • {avg_defining_per_job:.1f} per job average")
        
        return defining_df
    
    def load_job_skills_from_database(self, db_path: str) -> pd.DataFrame:
        """
        Load job-skill relationships from database for defining skills analysis.
        
        Args:
            db_path: Path to the SQLite database
            
        Returns:
            DataFrame with job-skill relationships including job and skill details
        """
        print("🔗 Loading job-skill relationships from database...")
        
        try:
            conn = sqlite3.connect(db_path)
            
            # Load job-skill relationships with job and skill details
            job_skills_query = """
            SELECT 
                j.JobProfileID,
                j.JobProfile,
                j.JobFunction,
                j.ManagementLevel,
                s.Skill_ID,
                s.Skill_Name,
                s.Category,
                s.Subcategory,
                s.SkillType
            FROM core_job_architecture j
            JOIN core_job_skill_requirements js ON j.JobProfileID = js.JobProfileID
            JOIN core_skills_taxonomy s ON js.Skill_ID = s.Skill_ID
            ORDER BY j.JobProfileID, s.Skill_Name
            """
            
            job_skills_df = pd.read_sql_query(job_skills_query, conn)
            conn.close()
            
            unique_jobs = job_skills_df['JobProfileID'].nunique()
            unique_skills = job_skills_df['Skill_ID'].nunique()
            avg_skills_per_job = len(job_skills_df) / unique_jobs if unique_jobs > 0 else 0
            
            print(f"   Loaded {len(job_skills_df):,} job-skill relationships")
            print(f"   {unique_jobs:,} jobs • {unique_skills:,} skills • {avg_skills_per_job:.1f} skills/job average")
            
            return job_skills_df
            
        except sqlite3.Error as e:
            self.logger.error(f"Database error while loading job-skill relationships: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error loading job-skill relationships: {e}")
            raise
    
    def get_defining_skills_summary(self, job_defining_skills: Dict[str, Set[str]]) -> Dict[str, Any]:
        """
        Generate summary statistics for job-specific defining skills.
        
        Args:
            job_defining_skills: Dict mapping job ID to set of defining skill names
            
        Returns:
            Dict with defining skills distribution statistics
        """
        total_jobs = len(job_defining_skills)
        total_relationships = sum(len(skills) for skills in job_defining_skills.values())
        
        # Calculate distribution of defining skills per job
        skills_per_job = [len(skills) for skills in job_defining_skills.values()]
        
        # Get unique defining skills across all jobs
        all_defining_skills = set()
        for skills in job_defining_skills.values():
            all_defining_skills.update(skills)
        
        summary = {
            'total_jobs_with_defining_skills': total_jobs,
            'total_defining_relationships': total_relationships,
            'unique_defining_skills': len(all_defining_skills),
            'avg_defining_skills_per_job': round(total_relationships / total_jobs, 1) if total_jobs > 0 else 0,
            'min_defining_skills_per_job': min(skills_per_job) if skills_per_job else 0,
            'max_defining_skills_per_job': max(skills_per_job) if skills_per_job else 0,
            'median_defining_skills_per_job': sorted(skills_per_job)[len(skills_per_job)//2] if skills_per_job else 0,
            'defining_skills_percentile_used': self.defining_skills_percentile
        }
        
        return summary
    
    def _apply_business_constraints(self, job_skill_count: int, base_percentile: float, 
                                  business_constraints: Dict[str, Any]) -> float:
        """
        Apply business constraints to limit defining skills based on job size.
        
        Args:
            job_skill_count: Number of skills in the job
            base_percentile: Base percentile from optimization
            business_constraints: Business constraints configuration
            
        Returns:
            Effective percentile to use (may be capped by business rules)
        """
        defining_limits = business_constraints.get('defining_skills_limits', {})
        if not defining_limits.get('enabled', False):
            return base_percentile
        
        job_categories = defining_limits.get('job_size_categories', {})
        
        # Determine job size category
        for category_name, category_config in job_categories.items():
            max_threshold = category_config.get('max_skills_threshold', float('inf'))
            if job_skill_count <= max_threshold:
                max_percentile = category_config.get('max_percentile_cap', base_percentile)
                effective_percentile = min(base_percentile, max_percentile)
                
                # Log constraint application if enabled
                if defining_limits.get('log_constraint_applications', False) and effective_percentile < base_percentile:
                    print(f"   🏢 Job size constraint applied: {job_skill_count} skills → {category_name} category → {effective_percentile:.1f}% (capped from {base_percentile:.1f}%)")
                
                return effective_percentile
        
        # Fallback - should not reach here with proper config
        return base_percentile
    
    def _get_defining_rank(self, 
                          job_id: str, 
                          skill_name: str, 
                          job_defining_skills: Dict[str, Set[str]], 
                          skill_universe: pd.DataFrame) -> int:
        """
        Get the rarity rank of a defining skill within its job profile.
        
        Args:
            job_id: Job profile ID
            skill_name: Skill name
            job_defining_skills: Dict mapping job ID to defining skills
            skill_universe: DataFrame with skill prevalence data
            
        Returns:
            Rank (1 = rarest defining skill for this job)
        """
        job_skills = job_defining_skills.get(job_id, set())
        
        if skill_name not in job_skills:
            return 0
        
        # Get prevalence for all defining skills in this job
        job_skill_prevalence = []
        for skill in job_skills:
            skill_info = skill_universe[skill_universe['Skill_Name'] == skill]
            if not skill_info.empty:
                prevalence = skill_info.iloc[0]['prevalence_percentage']
                job_skill_prevalence.append((skill, prevalence))
        
        # Sort by prevalence (ascending = rarest first), then by skill name for deterministic tie-breaking
        job_skill_prevalence.sort(key=lambda x: (x[1], x[0]))
        
        # Find rank of target skill
        for rank, (skill, _) in enumerate(job_skill_prevalence, 1):
            if skill == skill_name:
                return rank
                
        return 0
    
    def _get_optimal_parameters_for_job(self, job_skill_count: int) -> tuple[float, float]:
        """Get stratified optimal parameters for a specific job size."""
        
        # Try to get stratified parameters first
        from skill_similarity_engine.config.architectural_config_manager import get_config_manager
        config_manager = get_config_manager()
        
        stratified_config = config_manager.get_nested_value(
            'core', 'similarity_parameters', 'optuna_optimal', 'stratified_parameters'
        )
        
        if stratified_config:
            # Determine which layer this job belongs to
            if job_skill_count <= 15:
                layer_config = stratified_config.get('small_jobs', {})
            elif job_skill_count <= 30:
                layer_config = stratified_config.get('medium_jobs', {})
            elif job_skill_count <= 50:
                layer_config = stratified_config.get('large_jobs', {})
            else:
                layer_config = stratified_config.get('xlarge_jobs', {})
            
            if layer_config:
                return (
                    layer_config.get('defining_skills_percentile', self.defining_skills_percentile),
                    layer_config.get('defining_skills_multiplier', 1.5)  # default fallback multiplier
                )
        
        # Fallback to global parameters
        return (self.defining_skills_percentile, 1.5)  # default fallback multiplier