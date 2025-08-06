"""
Rarity-Weighted Similarity Algorithm

Core algorithm for calculating enhanced job similarity using rarity-weighted Jaccard similarity
with defining skills boost. This module contains the empirically-tuned algorithm extracted from
the experimental skill_intelligence_engine.py.

Based on hyperparameter tuning results:
- 20% percentile for defining skills identification
- 1.05x multiplier for shared defining skills (5% boost per skill)
- 0.76% average improvement, 12.5% positive impact rate
- 0.7714 smoothness score (optimal balance)
"""

import logging
from typing import Dict, Set, List, Any, Optional, Tuple
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
GENTLE_MULTIPLIER = _similarity_params['defining_skills_multiplier']


class RarityWeightedCalculator:
    """
    Calculates rarity-weighted job similarities using empirically-tuned parameters.
    
    This class implements the core algorithm for enhanced similarity calculation
    that provides better career pathway intelligence through defining skills boost.
    """
    
    def __init__(self, 
                 defining_skills_percentile: float = DEFINING_SKILLS_PERCENTILE,
                 gentle_multiplier: float = GENTLE_MULTIPLIER):
        """
        Initialize the rarity-weighted calculator.
        
        Args:
            defining_skills_percentile: Top % rarest skills per job (default: 8.8)
            gentle_multiplier: Multiplier for shared defining skills (default: 1.206)
        """
        self.defining_skills_percentile = defining_skills_percentile
        self.gentle_multiplier = gentle_multiplier
        self.logger = logging.getLogger(__name__)
        
    def calculate_skills_mobility_score(self,
                                      job_a_id: str,
                                      job_b_id: str,
                                      job_a_skills: Set[str], 
                                      job_b_skills: Set[str], 
                                      job_defining_skills: Dict[str, Set[str]]) -> Dict[str, Any]:
        """
        Calculate Skills-Based Mobility Score with empirically-tuned gentle multiplier.
        
        This measures career transition feasibility based on shared skills, with bonus weighting
        for rare/defining skills that indicate stronger pathway viability.
        
        Args:
            job_a_id: JobProfileID for source job
            job_b_id: JobProfileID for target job
            job_a_skills: Set of skill names for job A
            job_b_skills: Set of skill names for job B
            job_defining_skills: Dict mapping JobProfileID to Set of defining skills for that job
        
        Returns:
            Dict with mobility metrics and skills gap analysis
        """
        if not job_a_skills or not job_b_skills:
            return self._empty_mobility_result()
        
        # Calculate asymmetric Jaccard similarity (Job A to Job B pathway)
        # This measures what % of Job A's skills are present in Job B (career transition readiness)
        shared_skills = job_a_skills & job_b_skills
        simple_similarity = len(shared_skills) / len(job_a_skills) if job_a_skills else 0.0
        
        # Get defining skills for both jobs
        job_a_defining = job_defining_skills.get(job_a_id, set())
        job_b_defining = job_defining_skills.get(job_b_id, set())
        
        # Find shared defining skills (skills that are defining for EITHER job A OR job B)
        all_defining = job_a_defining | job_b_defining
        shared_defining_skills = []
        for skill in shared_skills:
            if skill in all_defining:
                shared_defining_skills.append(skill)
        
        # Apply gentle multiplier for each shared defining skill (multiplicative boost)
        # Each shared defining skill applies the multiplier: similarity * (1.206^count)
        if len(shared_defining_skills) > 0:
            # Apply the multiplier raised to the power of shared defining skills count
            multiplier_power = self.gentle_multiplier ** len(shared_defining_skills)
            weighted_similarity = simple_similarity * multiplier_power
            # Calculate the boost amount for reporting (how much the similarity was enhanced)
            defining_skill_boost = weighted_similarity - simple_similarity
        else:
            weighted_similarity = simple_similarity
            defining_skill_boost = 0.0
        
        # Note: No capping at 1.0 - corpus normalizer will handle final scaling
        # This preserves differentiation for jobs with strong defining skills advantages
        
        # Calculate comprehensive skills gap analysis
        skills_gap_analysis = self._analyze_skills_gap(job_a_skills, job_b_skills, all_defining)
        
        # Convert to 0-100 scale for business interpretation
        mobility_score_100 = round(weighted_similarity * 100, 1)
        baseline_score_100 = round(simple_similarity * 100, 1)
        
        return {
            'mobility_score': mobility_score_100,           # 0-100 scale
            'baseline_score': baseline_score_100,           # 0-100 scale  
            'weighted_similarity': round(weighted_similarity, 4),  # Keep for backwards compatibility
            'simple_similarity': round(simple_similarity, 4),      # Keep for backwards compatibility
            'shared_skills': list(shared_skills),
            'shared_defining_skills': shared_defining_skills,
            'total_shared_skills': len(shared_skills),
            'total_defining_shared': len(shared_defining_skills),
            'defining_skill_boost': round(defining_skill_boost, 4),
            **skills_gap_analysis  # Include comprehensive gap analysis
        }
    
    def calculate_all_similarities(self,
                                 job_ids: List[str],
                                 job_to_skills: Dict[str, Set[str]],
                                 job_defining_skills: Dict[str, Set[str]],
                                 show_progress: bool = True) -> List[Dict[str, Any]]:
        """
        Calculate rarity-weighted similarities for all job pairs (full asymmetric).
        
        This method focuses purely on the similarity calculation algorithm.
        Processing orchestration (chunking, parallelization) should be handled
        at the entry point level using utils modules.
        
        Args:
            job_ids: List of job profile IDs
            job_to_skills: Dict mapping job ID to set of skill names
            job_defining_skills: Dict mapping job ID to set of defining skill names
            show_progress: Whether to show basic progress tracking
            
        Returns:
            List of similarity records with mobility scores and gap analysis
        """
        # Create job pairs for full asymmetric comparison (A->B and B->A separately)
        job_pairs = []
        for job_a_id in job_ids:
            for job_b_id in job_ids:
                if job_a_id != job_b_id:  # Skip self-comparison
                    job_pairs.append((job_a_id, job_b_id))
        
        total_comparisons = len(job_pairs)
        self.logger.info(f"Processing {len(job_ids)} jobs for similarity calculations")
        self.logger.info(f"Total comparisons to compute: {total_comparisons:,}")
        
        similarities = []
        
        if show_progress:
            with progress_context(
                total=total_comparisons,
                desc="Enhanced Similarity Calculation",
                memory_tracking=True,
                show_tqdm=True
            ) as progress:
                for i, (job_a_id, job_b_id) in enumerate(job_pairs):
                    similarity = self.calculate_single_similarity(
                        job_a_id, job_b_id, job_to_skills, job_defining_skills
                    )
                    similarities.append(similarity)
                    
                    # Update progress periodically
                    if i % 1000 == 0:
                        progress.update(1000)
                
                # Update remaining progress
                remaining = len(job_pairs) % 1000
                if remaining > 0:
                    progress.update(remaining)
        else:
            # Simple processing without progress
            for i, (job_a_id, job_b_id) in enumerate(job_pairs):
                similarity = self.calculate_single_similarity(
                    job_a_id, job_b_id, job_to_skills, job_defining_skills
                )
                similarities.append(similarity)
                
                if i % 10000 == 0 and i > 0:
                    self.logger.info(f"Processed {i:,} comparisons...")
        
        self.logger.info(f"Generated {len(similarities):,} similarity records")
        return similarities
    
    def calculate_single_similarity(self, 
                                  job_a_id: str, 
                                  job_b_id: str,
                                  job_to_skills: Dict[str, Set[str]],
                                  job_defining_skills: Dict[str, Set[str]]) -> Dict[str, Any]:
        """
        Calculate similarity for a single job pair.
        
        This method is designed to be used by processing orchestrators
        that handle chunking, parallelization, and advanced progress tracking.
        
        Args:
            job_a_id: Source job ID
            job_b_id: Target job ID  
            job_to_skills: Dict mapping job ID to set of skill names
            job_defining_skills: Dict mapping job ID to set of defining skill names
            
        Returns:
            Similarity record dictionary for database insertion
        """
        job_a_skills = job_to_skills.get(job_a_id, set())
        job_b_skills = job_to_skills.get(job_b_id, set())
        
        if not job_a_skills or not job_b_skills:
            # Return empty similarity record for jobs without skills
            return {
                'similarity_id': f"{job_a_id}_{job_b_id}",
                'job_from': job_a_id,
                'job_to': job_b_id,
                'similarity_score': 0.0,
                'enhanced_similarity_score': 0.0,
                'rarity_weighted_score': 0.0,
                'shared_defining_skills_count': 0,
                'defining_skill_boost': 0.0,
                'shared_skills_count': 0,
                'total_skills_from': len(job_a_skills),
                'total_skills_to': len(job_b_skills),
                'skill_overlap_percentage': 0.0,
                'shared_skills': '',
                'shared_defining_skills': '',
                'skill_gap_analysis': 'No skills data available',
                'calculation_algorithm': 'rarity_weighted_v1.0'
            }
        
        # Calculate enhanced similarity A -> B
        mobility_analysis = self.calculate_skills_mobility_score(
            job_a_id,
            job_b_id,
            job_a_skills,
            job_b_skills,
            job_defining_skills
        )
        
        # Create similarity record for database (matching analytics_job_similarities schema)
        return {
            'similarity_id': f"{job_a_id}_{job_b_id}",
            'job_from': job_a_id,
            'job_to': job_b_id,
            'similarity_score': mobility_analysis['baseline_score'] / 100.0,  # Convert to 0-1 scale
            'enhanced_similarity_score': mobility_analysis['mobility_score'] / 100.0,  # Convert to 0-1 scale
            'rarity_weighted_score': mobility_analysis['mobility_score'] / 100.0,  # Same as enhanced
            'shared_defining_skills_count': mobility_analysis['total_defining_shared'],
            'defining_skill_boost': mobility_analysis['defining_skill_boost'],
            'shared_skills_count': mobility_analysis['total_shared_skills'],
            'total_skills_from': len(job_a_skills),
            'total_skills_to': len(job_b_skills),
            'skill_overlap_percentage': round((mobility_analysis['total_shared_skills'] / len(job_b_skills)) * 100, 1) if job_b_skills else 0,
            'shared_skills': ', '.join(mobility_analysis['matched_skills'][:10]),  # Limit for storage
            'shared_defining_skills': ', '.join(mobility_analysis['matched_defining_skills']),
            'skill_gap_analysis': f"Skills needed: {mobility_analysis['skills_to_develop']}, Defining gaps: {mobility_analysis['defining_skills_to_develop']}",
            'calculation_algorithm': 'rarity_weighted_v1.0'
        }

    
    def _analyze_skills_gap(self, 
                           job_a_skills: Set[str], 
                           job_b_skills: Set[str], 
                           defining_skills: Set[str]) -> Dict[str, Any]:
        """
        Comprehensive skills gap analysis for reskilling pathway conversations.
        
        Returns:
            Dict with matched/unmatched skills breakdown for both regular and defining skills
        """
        shared_skills = job_a_skills & job_b_skills
        
        # Regular skills analysis
        unmatched_a_skills = job_a_skills - job_b_skills  # Skills in A but not B
        unmatched_b_skills = job_b_skills - job_a_skills  # Skills in B but not A
        
        # Defining skills analysis
        shared_defining = []
        unmatched_a_defining = []
        unmatched_b_defining = []
        
        for skill in shared_skills:
            if skill in defining_skills:
                shared_defining.append(skill)
        
        for skill in unmatched_a_skills:
            if skill in defining_skills:
                unmatched_a_defining.append(skill)
        
        for skill in unmatched_b_skills:
            if skill in defining_skills:
                unmatched_b_defining.append(skill)
        
        return {
            'matched_skills': list(shared_skills),
            'unmatched_source_skills': list(unmatched_a_skills),
            'unmatched_target_skills': list(unmatched_b_skills),
            'matched_defining_skills': shared_defining,
            'unmatched_source_defining': unmatched_a_defining,
            'unmatched_target_defining': unmatched_b_defining,
            'skills_to_develop': len(unmatched_b_skills),        # Skills needed for target role
            'defining_skills_to_develop': len(unmatched_b_defining),  # Critical defining skills needed
            'transferable_advantage': len(shared_defining)        # Defining skills already possessed
        }
    
    def _empty_mobility_result(self) -> Dict[str, Any]:
        """Return empty mobility result for edge cases."""
        return {
            'mobility_score': 0.0,
            'baseline_score': 0.0,
            'weighted_similarity': 0.0,
            'simple_similarity': 0.0,
            'shared_skills': [],
            'shared_defining_skills': [],
            'total_shared_skills': 0,
            'total_defining_shared': 0,
            'defining_skill_boost': 0.0,
            'matched_skills': [],
            'unmatched_source_skills': [],
            'unmatched_target_skills': [],
            'matched_defining_skills': [],
            'unmatched_source_defining': [],
            'unmatched_target_defining': [],
            'skills_to_develop': 0,
            'defining_skills_to_develop': 0,
            'transferable_advantage': 0
        }