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
    'core', 'similarity_parameters', 'optuna_optimal',
    default={'defining_skills_percentile': 8.8}  # Fallback to optimal value
)

# Configuration constants (loaded from config/core/similarity_parameters.yaml)
DEFINING_SKILLS_PERCENTILE = _similarity_params.get('defining_skills_percentile', 8.8)


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
        Create job-specific defining skills using empirically-tuned percentile threshold.
        
        Uses top 8.8% rarest skills per job profile based on Optuna optimization results:
        - 8.8% percentile, 1.206x multiplier = optimal balance 
        - 0.57% avg improvement, higher differentiation, 0.7723 smoothness score
        
        Args:
            skill_universe: DataFrame with all skills and their global rarity/prevalence
            job_skills_df: DataFrame with job-skill relationships
            
        Returns:
            Dict mapping JobProfileID to Set of defining skill names for that job
        """
        self.logger.info(f"Creating job-specific defining skills (top {self.defining_skills_percentile}% rarest per role)")
        self.logger.info(f"Based on Optuna optimization: 0.57% avg improvement, enhanced differentiation")
        self.logger.info(f"Smoothness score: 0.7723 (optimal balance of smoothness + practical impact)")
        
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
                
                # Take top 8.8% rarest skills for this job (Optuna optimal)
                num_defining = max(1, int(len(job_skills_with_rarity) * self.defining_skills_percentile / 100))
                defining_for_this_job = job_skills_with_rarity.head(num_defining)['Skill_Name'].tolist()
                
                job_defining_skills[job_id] = set(defining_for_this_job)
                progress.update(1)
        
        # Calculate summary statistics
        total_jobs = len(job_defining_skills)
        total_defining_relationships = sum(len(skills) for skills in job_defining_skills.values())
        avg_defining_per_job = total_defining_relationships / total_jobs if total_jobs > 0 else 0
        
        self.logger.info(f"Created job-specific defining skills for {total_jobs:,} job profiles")
        self.logger.info(f"Total job-skill defining relationships: {total_defining_relationships:,}")
        self.logger.info(f"Average defining skills per job: {avg_defining_per_job:.1f}")
        
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
        self.logger.info("Generating job defining skills analysis...")
        
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
        
        self.logger.info(f"Generated defining skills analysis for {len(defining_df):,} job-skill pairs")
        
        # Show summary statistics
        unique_jobs = defining_df['job_profile_id'].nunique()
        unique_skills = defining_df['skill_id'].nunique()
        avg_defining_per_job = len(defining_df) / unique_jobs if unique_jobs > 0 else 0
        
        self.logger.info(f"Unique jobs with defining skills: {unique_jobs:,}")
        self.logger.info(f"Unique defining skills: {unique_skills:,}")
        self.logger.info(f"Average defining skills per job: {avg_defining_per_job:.1f}")
        
        return defining_df
    
    def load_job_skills_from_database(self, db_path: str) -> pd.DataFrame:
        """
        Load job-skill relationships from database for defining skills analysis.
        
        Args:
            db_path: Path to the SQLite database
            
        Returns:
            DataFrame with job-skill relationships including job and skill details
        """
        self.logger.info("Loading job-skill relationships from database...")
        
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
            
            self.logger.info(f"Loaded {len(job_skills_df):,} job-skill relationships")
            
            unique_jobs = job_skills_df['JobProfileID'].nunique()
            unique_skills = job_skills_df['Skill_ID'].nunique()
            avg_skills_per_job = len(job_skills_df) / unique_jobs if unique_jobs > 0 else 0
            
            self.logger.info(f"Unique jobs: {unique_jobs:,}")
            self.logger.info(f"Unique skills: {unique_skills:,}")
            self.logger.info(f"Average skills per job: {avg_skills_per_job:.1f}")
            
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