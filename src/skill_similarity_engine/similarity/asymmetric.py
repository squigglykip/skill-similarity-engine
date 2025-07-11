from typing import Dict, List, Optional, Any
import pandas as pd
from ..models.jobs import JobArchitecture
from ..models.skills import SkillTaxonomy
from ..config.architectural_config_manager import get_config_manager

class AsymmetricCoverageCalculator:
    """
    Calculates asymmetric skill coverage between jobs.
    
    This class focuses purely on skill overlap calculation without any weighting
    or context modifiers. It provides the foundation for precomputation of base
    similarity matrices.
    
    For weighted similarity calculations and context-aware querying, use the
    dedicated query modules (to be implemented separately).
    """
    
    def __init__(self, job_architecture: JobArchitecture):
        """
        Initialize the calculator.
        
        Args:
            job_architecture: Job architecture containing all jobs and their skills
        """
        self.job_architecture = job_architecture
        self.config_manager = get_config_manager()

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
