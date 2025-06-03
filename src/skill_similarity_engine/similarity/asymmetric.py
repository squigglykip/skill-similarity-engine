from typing import Dict, List, Optional
import pandas as pd
from ..models.jobs import JobArchitecture
from ..models.skills import SkillTaxonomy

class AsymmetricCoverageCalculator:
    """
    Calculates asymmetric skill coverage between jobs, with optional weighting and blending of other factors.
    Supports weighting by skill category/type and blending in seniority, role track, and location similarity.
    """
    def __init__(self, job_architecture: JobArchitecture, skill_taxonomy: Optional[SkillTaxonomy] = None,
                 skill_category_weights: Optional[Dict[str, float]] = None,
                 skill_type_weights: Optional[Dict[str, float]] = None,
                 seniority_weight: float = 0.0,
                 role_track_weight: float = 0.0,
                 location_weight: float = 0.0):
        self.job_architecture = job_architecture
        self.skill_taxonomy = skill_taxonomy
        self.skill_category_weights = skill_category_weights or {}
        self.skill_type_weights = skill_type_weights or {}
        self.seniority_weight = seniority_weight
        self.role_track_weight = role_track_weight
        self.location_weight = location_weight

    def get_skill_weight(self, skill_id):
        # Prefer category, fallback to type, fallback to 1.0
        if self.skill_category_weights and self.skill_taxonomy:
            cat = getattr(self.skill_taxonomy.skills[skill_id], 'category_id', None)
            cat_key = str(cat) if cat is not None else 'UNKNOWN'
            return self.skill_category_weights.get(cat_key, 1.0)
        elif self.skill_type_weights and self.skill_taxonomy:
            typ = getattr(self.skill_taxonomy.skills[skill_id], 'skill_type', None)
            typ_key = str(typ) if typ is not None else 'UNKNOWN'
            return self.skill_type_weights.get(typ_key, 1.0)
        else:
            return 1.0

    def calculate_job_coverage(self, job1_id: str, job2_id: str) -> float:
        """
        Calculate the proportion of job1's skills that are present in job2.
        Optionally applies weighting if weights are provided.
        """
        job1 = self.job_architecture.jobs[job1_id]
        job2 = self.job_architecture.jobs[job2_id]
        skills1 = set(job1.skills.keys())
        skills2 = set(job2.skills.keys())
        if not skills1:
            return 0.0
        shared = skills1 & skills2
        numerator = sum(self.get_skill_weight(s) for s in shared)
        denominator = sum(self.get_skill_weight(s) for s in skills1)
        return numerator / denominator if denominator > 0 else 0.0

    def _calculate_seniority_similarity(self, job1, job2) -> float:
        # Both jobs must have 'level' attribute (int or enum with .numeric)
        level1 = getattr(job1, 'level', None)
        level2 = getattr(job2, 'level', None)
        if level1 is None or level2 is None:
            return 1.0  # No penalty if missing
        try:
            val1 = level1.numeric if hasattr(level1, 'numeric') else (level1.value if hasattr(level1, 'value') else int(level1))
            val2 = level2.numeric if hasattr(level2, 'numeric') else (level2.value if hasattr(level2, 'value') else int(level2))
        except Exception:
            return 1.0
        diff = val2 - val1
        if diff == 0:
            return 1.0
        elif diff == 1:
            return 0.7
        elif diff > 1:
            return max(0.0, 0.7 - (diff - 1) * 0.1)
        elif diff == -1:
            return 0.1
        else:
            return 0.0

    def _calculate_role_track_similarity(self, job1, job2) -> float:
        # Both jobs must have 'role_track' attribute
        rt1 = getattr(job1, 'role_track', None)
        rt2 = getattr(job2, 'role_track', None)
        if rt1 is None or rt2 is None:
            return 1.0
        if rt1 == rt2:
            return 1.0
        # Assume IC to Leadership is progression, reverse is regression
        if str(rt1).lower().startswith('ind') and str(rt2).lower().startswith('lead'):
            return 0.5
        else:
            return 0.1

    def _calculate_location_similarity(self, job1, job2) -> float:
        loc1 = getattr(job1, 'location', None)
        loc2 = getattr(job2, 'location', None)
        if not loc1 or not loc2:
            return 1.0
        if str(loc1).lower() == str(loc2).lower():
            return 1.0
        return 0.3

    def calculate_job_similarity(self, job1_id: str, job2_id: str) -> float:
        job1 = self.job_architecture.jobs[job1_id]
        job2 = self.job_architecture.jobs[job2_id]
        # Skill coverage
        skill_coverage = self.calculate_job_coverage(job1_id, job2_id)
        # Other factors
        seniority_sim = self._calculate_seniority_similarity(job1, job2)
        role_track_sim = self._calculate_role_track_similarity(job1, job2)
        location_sim = self._calculate_location_similarity(job1, job2)
        # Weights
        skill_weight = 1.0
        total_weight = skill_weight + self.seniority_weight + self.role_track_weight + self.location_weight
        weighted_similarity = (
            skill_coverage * skill_weight +
            seniority_sim * self.seniority_weight +
            role_track_sim * self.role_track_weight +
            location_sim * self.location_weight
        ) / total_weight
        return weighted_similarity

    def calculate_coverage_matrix(self) -> pd.DataFrame:
        """
        Calculate asymmetric coverage for all job pairs (job_from, job_to), excluding self-comparisons.
        Returns a DataFrame with columns: job_from, job_to, similarity
        """
        job_ids = list(self.job_architecture.jobs.keys())
        results = []
        for job_from in job_ids:
            for job_to in job_ids:
                if job_from == job_to:
                    continue
                similarity = self.calculate_job_similarity(job_from, job_to)
                results.append({
                    'job_from': job_from,
                    'job_to': job_to,
                    'similarity': similarity
                })
        return pd.DataFrame(results) 