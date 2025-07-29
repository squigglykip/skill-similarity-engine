from typing import Dict, List, Optional, Any, Set
import pandas as pd
import sqlite3
from pathlib import Path
from ..models.jobs import JobArchitecture
from ..models.skills import SkillTaxonomy
from ..config.architectural_config_manager import get_config_manager
from ..error_handling.recovery import retry, circuit_breaker, fallback_on_failure

class AsymmetricCoverageCalculator:
    """
    Calculates asymmetric skill coverage between jobs with unified similarity capabilities.
    
    This class provides both basic skill overlap calculation and sophisticated unified
    algorithms with defining skills boost. All parameters are configuration-driven
    following our modular architecture philosophy.
    
    The unified algorithm is based on empirically-tuned parameters from research notebooks
    that show 0.76% improvement over basic Jaccard, with all values externalized to configuration.
    
    For weighted similarity calculations and context-aware querying, use the
    dedicated query modules (to be implemented separately).
    """
    
    def __init__(self, job_architecture: JobArchitecture, skill_universe_df: Optional[pd.DataFrame] = None):
        """
        Initialize the calculator.
        
        Args:
            job_architecture: Job architecture containing all jobs and their skills
            skill_universe_df: Optional DataFrame with skill rarity data for enhanced algorithms
        """
        self.job_architecture = job_architecture
        self.config_manager = get_config_manager()
        self.skill_universe_df = skill_universe_df
        self._job_defining_skills = None  # Lazy-loaded cache
        
        # Load rarity-weighted similarity configuration
        self.rarity_weighted_config = self._load_rarity_weighted_config()

    def _load_rarity_weighted_config(self) -> Dict[str, Any]:
        """Load rarity-weighted similarity parameters from configuration."""
        config = self.config_manager.get_nested_value(
            'similarity', 'rarity_weighted_algorithms'
        )
        
        if not config:
            raise ValueError(
                "Missing required configuration section: similarity.rarity_weighted_algorithms. "
                "Please ensure the configuration file includes all required parameters."
            )
        
        # Validate required configuration parameters
        required_params = ['defining_skills_percentile', 'gentle_multiplier', 'rarity_thresholds']
        missing_params = [param for param in required_params if param not in config]
        
        if missing_params:
            raise ValueError(
                f"Missing required configuration parameters: {missing_params}. "
                f"Please ensure all required parameters are defined in similarity.rarity_weighted_algorithms"
            )
        
        # Validate parameter ranges
        if not (1 <= config['defining_skills_percentile'] <= 100):
            raise ValueError(
                f"defining_skills_percentile must be between 1 and 100, got: {config['defining_skills_percentile']}"
            )
        
        if config['gentle_multiplier'] <= 1.0:
            raise ValueError(
                f"gentle_multiplier must be greater than 1.0, got: {config['gentle_multiplier']}"
            )
        
        if not isinstance(config['rarity_thresholds'], dict):
            raise ValueError("rarity_thresholds must be a dictionary")
        
        return config

    # ============================================================================
    # EXISTING METHODS - PRESERVED FOR BACKWARD COMPATIBILITY
    # ============================================================================

    def calculate_job_coverage(self, job1_id: str, job2_id: str) -> float:
        """
        Calculate the proportion of job1's skills that are present in job2.
        
        This is the core asymmetric skill overlap calculation:
        - Returns the percentage of job1's skills that job2 also has
        - No weighting, no context modifiers - pure skill set overlap
        
        Args:
            job1_id: Source job ID (skills we're measuring coverage for)
            job2_id: Target job ID (skills we're checking against)
            
        Returns:
            float: Proportion of job1's skills present in job2 (0.0 to 1.0)
        """
        job1 = self.job_architecture.jobs[job1_id]
        job2 = self.job_architecture.jobs[job2_id]
        
        skills1 = set(job1.skills.keys())
        skills2 = set(job2.skills.keys())
        
        if not skills1:
            return 0.0
            
        shared_skills = skills1 & skills2
        return len(shared_skills) / len(skills1)

    def calculate_symmetric_similarity(self, job1_id: str, job2_id: str) -> float:
        """
        Calculate symmetric similarity between two jobs using Jaccard coefficient.
        
        Jaccard = |intersection| / |union|
        
        Args:
            job1_id: First job ID
            job2_id: Second job ID
            
        Returns:
            float: Jaccard similarity coefficient (0.0 to 1.0)
        """
        job1 = self.job_architecture.jobs[job1_id]
        job2 = self.job_architecture.jobs[job2_id]
        
        skills1 = set(job1.skills.keys())
        skills2 = set(job2.skills.keys())
        
        if not skills1 and not skills2:
            return 1.0  # Both jobs have no skills
        
        shared_skills = skills1 & skills2
        total_skills = skills1 | skills2
        
        return len(shared_skills) / len(total_skills) if total_skills else 0.0

    # ============================================================================
    # ENHANCED SIMILARITY METHODS - NEW SOPHISTICATED ALGORITHMS
    # ============================================================================

    @retry(max_attempts=3)
    @circuit_breaker(failure_threshold=3)
    def calculate_rarity_weighted_similarity(self, job_a_skills: Set[str], job_b_skills: Set[str], 
                                           defining_skills_map: Optional[Dict[str, Set[str]]] = None) -> Dict[str, Any]:
        """
        Calculate unified similarity with defining skills boost.
        
        Based on empirically-tuned parameters from research notebooks with 0.76% average 
        improvement over basic Jaccard and 12.5% positive improvement rate.
        
        All parameters (percentile threshold, multiplier) are loaded from configuration
        to ensure flexibility and avoid hardcoded values.
        
        This is the SINGLE unified algorithm that replaces basic asymmetric comparison.
        
        Args:
            job_a_skills: Set of skill names for job A
            job_b_skills: Set of skill names for job B
            defining_skills_map: Optional pre-computed defining skills map (auto-generated if not provided)
            
        Returns:
            Dict with similarity metrics including the unified enhanced score
        """
        if not job_a_skills or not job_b_skills:
            return self._empty_similarity_result()
        
        # Step 1: Calculate basic Jaccard similarity (baseline)
        shared_skills = job_a_skills & job_b_skills
        total_skills = job_a_skills | job_b_skills
        basic_similarity = len(shared_skills) / len(total_skills) if total_skills else 0.0
        
        # Step 2: Get defining skills for both jobs (top percentile rarest skills per job)
        if defining_skills_map is not None:
            # Use provided defining skills map
            job_a_defining = set()
            job_b_defining = set()
            for job_id, defining_skills in defining_skills_map.items():
                # Find which job this defining skills set belongs to by checking skill overlap
                if len(defining_skills & job_a_skills) > len(defining_skills & job_b_skills):
                    job_a_defining.update(defining_skills)
                else:
                    job_b_defining.update(defining_skills)
        else:
            # Auto-generate defining skills using skill universe data
            job_a_defining = self._get_defining_skills_for_skillset(job_a_skills)
            job_b_defining = self._get_defining_skills_for_skillset(job_b_skills)
        
        # Step 3: Find shared defining skills (skills that are defining for EITHER job A OR job B)
        all_defining = job_a_defining | job_b_defining
        shared_defining_skills = [skill for skill in shared_skills if skill in all_defining]
        
        # Step 4: Apply gentle multiplier boost from configuration
        gentle_multiplier = self.rarity_weighted_config['gentle_multiplier']
        defining_skill_boost = len(shared_defining_skills) * (gentle_multiplier - 1.0)
        enhanced_similarity = basic_similarity * (1.0 + defining_skill_boost)
        
        # Step 5: Cap at 1.0 to maintain similarity interpretation
        enhanced_similarity = min(1.0, enhanced_similarity)
        
        return {
            'basic_similarity': round(basic_similarity, 4),
            'enhanced_similarity': round(enhanced_similarity, 4),
            'rarity_weighted_score': round(enhanced_similarity, 4),  # Same as enhanced for backward compatibility
            'shared_defining_skills_count': len(shared_defining_skills),
            'defining_skill_boost': round(defining_skill_boost, 4),
            'shared_skills': list(shared_skills),
            'shared_defining_skills': shared_defining_skills
        }

    def _get_defining_skills_for_skillset(self, skills: Set[str]) -> Set[str]:
        """
        Get defining skills for a given skillset (top percentile rarest skills).
        
        The percentile threshold is loaded from configuration to ensure flexibility.
        
        Args:
            skills: Set of skill names
            
        Returns:
            Set of defining skill names (top percentile rarest based on configuration)
        """
        if self.skill_universe_df is None or not skills:
            return set()
        
        # Get rarity info for these skills
        skills_with_rarity = self.skill_universe_df[
            self.skill_universe_df['Skill_Name'].isin(skills)
        ].copy()
        
        if skills_with_rarity.empty:
            return set()
        
        # Sort by prevalence (ascending = rarest first)
        skills_with_rarity = skills_with_rarity.sort_values('prevalence_percentage')
        
        # Take top percentile rarest skills from configuration
        percentile_threshold = self.rarity_weighted_config['defining_skills_percentile']
        num_defining = max(1, len(skills_with_rarity) * percentile_threshold // 100)
        defining_skills = skills_with_rarity.head(num_defining)['Skill_Name'].tolist()
        
        return set(defining_skills)

    # Backward compatibility method
    def calculate_enhanced_similarity(self, job_a_skills: Set[str], job_b_skills: Set[str], 
                                    defining_skills_map: Optional[Dict[str, Set[str]]] = None) -> Dict[str, Any]:
        """
        Backward compatibility wrapper for calculate_rarity_weighted_similarity.
        
        DEPRECATED: Use calculate_rarity_weighted_similarity instead.
        """
        return self.calculate_rarity_weighted_similarity(job_a_skills, job_b_skills, defining_skills_map)

    def create_job_defining_skills_map(self, job_ids: Optional[List[str]] = None) -> Dict[str, Set[str]]:
        """
        Create a map of job IDs to their defining skills using cached computation.
        
        Args:
            job_ids: Optional list of job IDs to create map for. If None, uses all jobs.
        
        Returns:
            Dict mapping job_profile_id to Set of defining skill names
        """
        if self._job_defining_skills is not None and job_ids is None:
            return self._job_defining_skills
        
        if self.skill_universe_df is None:
            job_list = job_ids or list(self.job_architecture.jobs.keys())
            return {job_id: set() for job_id in job_list}
        
        job_list = job_ids or list(self.job_architecture.jobs.keys())
        defining_skills_map = {}
        
        for job_id in job_list:
            if job_id in self.job_architecture.jobs:
                job = self.job_architecture.jobs[job_id]
                job_skills = set(job.skills.keys())
                defining_skills_map[job_id] = self._get_defining_skills_for_skillset(job_skills)
            else:
                defining_skills_map[job_id] = set()
        
        # Cache if we computed for all jobs
        if job_ids is None:
            self._job_defining_skills = defining_skills_map
        
        return defining_skills_map

    def _empty_similarity_result(self) -> Dict[str, Any]:
        """Return empty similarity result for edge cases."""
        return {
            'basic_similarity': 0.0,
            'enhanced_similarity': 0.0,
            'rarity_weighted_score': 0.0,
            'shared_defining_skills_count': 0,
            'defining_skill_boost': 0.0,
            'shared_skills': [],
            'shared_defining_skills': []
        }

    # ============================================================================
    # EXISTING METHODS CONTINUED - PRESERVED FOR BACKWARD COMPATIBILITY
    # ============================================================================

    def get_skill_overlap_details(self, job1_id: str, job2_id: str) -> Dict[str, Any]:
        """
        Get detailed information about skill overlap between two jobs.
        
        Args:
            job1_id: First job ID
            job2_id: Second job ID
            
        Returns:
            Dictionary containing detailed overlap information
        """
        job1 = self.job_architecture.jobs[job1_id]
        job2 = self.job_architecture.jobs[job2_id]
        
        skills1 = set(job1.skills.keys())
        skills2 = set(job2.skills.keys())
        
        shared_skills = skills1 & skills2
        job1_unique = skills1 - skills2
        job2_unique = skills2 - skills1
        
        return {
            'job1_total_skills': len(skills1),
            'job2_total_skills': len(skills2),
            'shared_skills': len(shared_skills),
            'job1_unique_skills': len(job1_unique),
            'job2_unique_skills': len(job2_unique),
            'job1_coverage': len(shared_skills) / len(skills1) if skills1 else 0.0,
            'job2_coverage': len(shared_skills) / len(skills2) if skills2 else 0.0,
            'jaccard_similarity': len(shared_skills) / len(skills1 | skills2) if (skills1 | skills2) else 0.0,
            'shared_skill_ids': list(shared_skills),
            'job1_unique_skill_ids': list(job1_unique),
            'job2_unique_skill_ids': list(job2_unique)
        }

    def calculate_coverage_matrix(self, exclude_self_comparison: bool = True) -> pd.DataFrame:
        """
        Calculate asymmetric coverage for all job pairs.
        
        Args:
            exclude_self_comparison: Whether to exclude job-to-self comparisons
            
        Returns:
            DataFrame with columns: job_from, job_to, coverage
        """
        job_ids = list(self.job_architecture.jobs.keys())
        results = []
        
        for job_from in job_ids:
            for job_to in job_ids:
                if exclude_self_comparison and job_from == job_to:
                    continue
                
                coverage = self.calculate_job_coverage(job_from, job_to)
                results.append({
                    'job_from': job_from,
                    'job_to': job_to,
                    'coverage': coverage
                })
        
        return pd.DataFrame(results)

    def find_most_similar_jobs(self, job_id: str, top_n: Optional[int] = None, 
                              similarity_method: str = 'asymmetric') -> List[Dict[str, Any]]:
        """
        Find the most similar jobs to a given job.
        
        Args:
            job_id: Reference job ID
            top_n: Number of top similar jobs to return (uses config default if None)
            similarity_method: 'asymmetric' (coverage) or 'symmetric' (Jaccard)
            
        Returns:
            List of dictionaries with job_id and similarity score, sorted by similarity
        """
        # Get top_n from configuration if not provided
        if top_n is None:
            asymmetric_config = self.config_manager.get_similarity_asymmetric_config()
            top_n = asymmetric_config.get('default_top_n_results', 10)
        
        job_ids = [jid for jid in self.job_architecture.jobs.keys() if jid != job_id]
        similarities = []
        
        for other_job_id in job_ids:
            if similarity_method == 'asymmetric':
                # How much of the reference job's skills does the other job have?
                similarity = self.calculate_job_coverage(job_id, other_job_id)
            elif similarity_method == 'symmetric':
                similarity = self.calculate_symmetric_similarity(job_id, other_job_id)
            else:
                raise ValueError(f"Unknown similarity method: {similarity_method}")
            
            similarities.append({
                'job_id': other_job_id,
                'similarity': similarity
            })
        
        # Sort by similarity (descending) and return top N
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities[:top_n]

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the job architecture and skill distribution.
        
        Returns:
            Dictionary with various statistics
        """
        job_ids = list(self.job_architecture.jobs.keys())
        skill_counts = [len(self.job_architecture.jobs[jid].skills) for jid in job_ids]
        
        # Get all unique skills across all jobs
        all_skills = set()
        for job_id in job_ids:
            all_skills.update(self.job_architecture.jobs[job_id].skills.keys())
        
        return {
            'total_jobs': len(job_ids),
            'total_unique_skills': len(all_skills),
            'avg_skills_per_job': sum(skill_counts) / len(skill_counts) if skill_counts else 0,
            'min_skills_per_job': min(skill_counts) if skill_counts else 0,
            'max_skills_per_job': max(skill_counts) if skill_counts else 0,
            'total_job_skill_assignments': sum(skill_counts),
        } 
