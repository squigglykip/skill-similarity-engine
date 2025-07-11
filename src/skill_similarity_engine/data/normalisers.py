"""
Data normalisation strategies for skill proficiency levels.

This module provides various methods for normalising skill data, including
min-max scaling, boolean normalisation, and TF-IDF style weighting.

Architecture: Configuration-Driven Design Pattern following PTH's enterprise patterns
"""

import math
from collections import Counter
from typing import Dict, List, Optional, Set, Tuple, Union

import numpy as np

from ..config.architectural_config_manager import get_config_manager
from ..models.jobs import Job, JobArchitecture
from ..models.skills import Skill, SkillTaxonomy


class MinMaxScaler:
    """
    Min-max scaler for normalising skill proficiency levels.
    
    Attributes:
        min_value: Minimum proficiency value (default: 0)
        max_value: Maximum proficiency value (default: 5)
        target_min: Target minimum value after scaling (default: 0)
        target_max: Target maximum value after scaling (default: 1)
    """
    
    def __init__(
        self, 
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
        target_min: Optional[float] = None,
        target_max: Optional[float] = None
    ):
        """
        Initialize the min-max scaler using architectural configuration.
        
        Args:
            min_value: Minimum proficiency value (default: from configuration)
            max_value: Maximum proficiency value (default: from configuration)
            target_min: Target minimum value after scaling (default: from configuration)
            target_max: Target maximum value after scaling (default: from configuration)
        """
        # Load configuration values
        try:
            config_manager = get_config_manager()
            scaling_config = config_manager.get_nested_value('data', 'normalisation', 'min_max_scaling', default={})
            
            self.min_value = min_value if min_value is not None else scaling_config.get('min_value', 0)
            self.max_value = max_value if max_value is not None else scaling_config.get('max_value', 5)
            self.target_min = target_min if target_min is not None else scaling_config.get('target_min', 0.0)
            self.target_max = target_max if target_max is not None else scaling_config.get('target_max', 1.0)
        except Exception:
            # Fallback to hardcoded defaults if configuration unavailable
            self.min_value = min_value if min_value is not None else 0
            self.max_value = max_value if max_value is not None else 5
            self.target_min = target_min if target_min is not None else 0.0
            self.target_max = target_max if target_max is not None else 1.0
        
        # Check for division by zero
        if self.max_value == self.min_value:
            raise ValueError("Min and max values cannot be equal")
    
    def scale(self, value: int) -> float:
        """
        Scale a single proficiency value.
        
        Args:
            value: Proficiency value to scale
            
        Returns:
            Scaled value between target_min and target_max
        """
        # Handle out-of-range values
        clamped_value = max(self.min_value, min(self.max_value, value))
        
        # Apply min-max scaling formula
        scale_factor = (self.target_max - self.target_min) / (self.max_value - self.min_value)
        return self.target_min + scale_factor * (clamped_value - self.min_value)
    
    def scale_dict(self, proficiency_dict: Dict[str, int]) -> Dict[str, float]:
        """
        Scale a dictionary of skill proficiency values.
        
        Args:
            proficiency_dict: Dictionary mapping skill IDs to proficiency values
            
        Returns:
            Dictionary with scaled proficiency values
        """
        return {
            skill_id: self.scale(proficiency)
            for skill_id, proficiency in proficiency_dict.items()
        }


class BooleanNormaliser:
    """
    Normaliser that converts skill proficiency levels to boolean values.
    
    Attributes:
        threshold: Minimum proficiency value to be considered as having the skill
    """
    
    def __init__(self, threshold: Optional[int] = None):
        """
        Initialize the boolean normaliser using architectural configuration.
        
        Args:
            threshold: Minimum proficiency value to be considered as having the skill (default: from configuration)
        """
        # Load threshold from configuration
        try:
            config_manager = get_config_manager()
            boolean_config = config_manager.get_nested_value('data', 'normalisation', 'boolean_normalisation', default={})
            self.threshold = threshold if threshold is not None else boolean_config.get('threshold', 1)
        except Exception:
            # Fallback to default if configuration unavailable
            self.threshold = threshold if threshold is not None else 1
    
    def normalise(self, value: int) -> float:
        """
        Convert a proficiency value to a boolean value (0.0 or 1.0).
        
        Args:
            value: Proficiency value to normalise
            
        Returns:
            1.0 if value >= threshold, 0.0 otherwise
        """
        return 1.0 if value >= self.threshold else 0.0
    
    def normalise_dict(self, proficiency_dict: Dict[str, int]) -> Dict[str, float]:
        """
        Normalise a dictionary of skill proficiency values.
        
        Args:
            proficiency_dict: Dictionary mapping skill IDs to proficiency values
            
        Returns:
            Dictionary with boolean proficiency values
        """
        return {
            skill_id: self.normalise(proficiency)
            for skill_id, proficiency in proficiency_dict.items()
        }


class TfIdfWeighter:
    """
    TF-IDF style weighter for skill proficiency levels.
    
    Attributes:
        idf_values: Dictionary mapping skill IDs to IDF values
        skill_taxonomy: The skill taxonomy containing all skills
    """
    
    def __init__(self, skill_taxonomy: SkillTaxonomy, job_architecture: JobArchitecture):
        """
        Initialize the TF-IDF weighter.
        
        Args:
            skill_taxonomy: The skill taxonomy containing all skills
            job_architecture: The job architecture containing all jobs
        """
        self.skill_taxonomy = skill_taxonomy
        self.idf_values: Dict[str, float] = self._calculate_idf(job_architecture)
    
    def _calculate_idf(self, job_architecture: JobArchitecture) -> Dict[str, float]:
        """
        Calculate IDF (Inverse Document Frequency) values for all skills.
        
        Args:
            job_architecture: The job architecture containing all jobs
            
        Returns:
            Dictionary mapping skill IDs to IDF values
        """
        # Count in how many jobs each skill appears
        skill_doc_counts = Counter()
        total_jobs = len(job_architecture.jobs)
        
        for job in job_architecture.jobs.values():
            # Count each skill only once per job
            for skill_id in job.skills:
                skill_doc_counts[skill_id] += 1
        
        # Calculate IDF values for each skill
        idf_values = {}
        for skill_id in self.skill_taxonomy.skills:
            doc_count = skill_doc_counts.get(skill_id, 0)
            # Add 1 to avoid division by zero (smoothing)
            idf_values[skill_id] = math.log((total_jobs + 1) / (doc_count + 1)) + 1
        
        return idf_values
    
    def weight_dict(self, proficiency_dict: Dict[str, float]) -> Dict[str, float]:
        """
        Apply TF-IDF weighting to a dictionary of skill proficiency values.
        
        Args:
            proficiency_dict: Dictionary mapping skill IDs to proficiency values
            
        Returns:
            Dictionary with weighted proficiency values
        """
        # Calculate sum of proficiencies for TF component
        total_proficiency = sum(proficiency_dict.values())
        
        if total_proficiency == 0:
            return {}
        
        weighted_dict = {}
        for skill_id, proficiency in proficiency_dict.items():
            # TF = proficiency / total proficiency
            tf = proficiency / total_proficiency
            # Get IDF value (default to 1.0 if not found)
            idf = self.idf_values.get(skill_id, 1.0)
            # Apply TF-IDF weighting
            weighted_dict[skill_id] = tf * idf
        
        return weighted_dict


class CategoryWeighter:
    """
    Weighter that applies importance weights based on skill categories.
    
    Attributes:
        importance_weights: Dictionary mapping skill categories to importance weights
        skill_taxonomy: The skill taxonomy containing all skills
    """
    
    def __init__(self, skill_taxonomy: SkillTaxonomy, importance_weights: Dict[str, float] = None):
        """
        Initialize the category weighter.
        
        Args:
            skill_taxonomy: The skill taxonomy containing all skills
            importance_weights: Dictionary mapping skill categories to importance weights
        """
        self.skill_taxonomy = skill_taxonomy
        
        if importance_weights is None:
            # Use weights from configuration if not provided
            try:
                config_manager = get_config_manager()
                normalisation_config = config_manager.get_nested_value('data', 'normalisation', default={})
                self.importance_weights = normalisation_config.get('importance_weights', {
                    "Technical": 1.0,
                    "Soft": 1.0,
                    "Domain": 1.0,
                    "Methodology": 1.0,
                    "Tool": 1.0,
                    "Certification": 1.0,
                    "Other": 1.0
                })
            except Exception:
                # Fallback to default weights if configuration unavailable
                self.importance_weights = {
                    "Technical": 1.0,
                    "Soft": 1.0,
                    "Domain": 1.0,
                    "Methodology": 1.0,
                    "Tool": 1.0,
                    "Certification": 1.0,
                    "Other": 1.0
                }
        else:
            self.importance_weights = importance_weights
    
    def get_category_for_skill(self, skill_id: str) -> str:
        """
        Get the category for a skill.
        
        Args:
            skill_id: ID of the skill
            
        Returns:
            Category of the skill, or "Other" if not found
        """
        if skill_id not in self.skill_taxonomy.skills:
            return "Other"
        
        skill = self.skill_taxonomy.skills[skill_id]
        
        if not skill.category_id or skill.category_id not in self.skill_taxonomy.categories:
            return "Other"
        
        category = self.skill_taxonomy.categories[skill.category_id]
        return category.name
    
    def weight_dict(self, proficiency_dict: Dict[str, float]) -> Dict[str, float]:
        """
        Apply category weights to a dictionary of skill proficiency values.
        
        Args:
            proficiency_dict: Dictionary mapping skill IDs to proficiency values
            
        Returns:
            Dictionary with weighted proficiency values
        """
        weighted_dict = {}
        
        for skill_id, proficiency in proficiency_dict.items():
            category = self.get_category_for_skill(skill_id)
            # Get importance weight (default to 1.0 if not found)
            weight = self.importance_weights.get(category, 1.0)
            # Apply category weight
            weighted_dict[skill_id] = proficiency * weight
        
        return weighted_dict


class SkillNormaliser:
    """
    Combined normaliser that applies multiple normalisation strategies.
    
    Attributes:
        skill_taxonomy: The skill taxonomy containing all skills
        job_architecture: The job architecture containing all jobs
        min_max_scaler: The min-max scaler for scaling proficiency levels
        boolean_normaliser: The boolean normaliser for boolean normalisation
        tfidf_weighter: The TF-IDF weighter for TF-IDF style weighting
        category_weighter: The category weighter for applying importance weights
    """
    
    def __init__(
        self,
        skill_taxonomy: SkillTaxonomy,
        job_architecture: JobArchitecture,
        use_min_max_scaling: bool = None,
        use_boolean_normalisation: bool = None,
        use_tfidf_weighting: bool = None,
        importance_weights: Dict[str, float] = None
    ):
        """
        Initialize the skill normaliser.
        
        Args:
            skill_taxonomy: The skill taxonomy containing all skills
            job_architecture: The job architecture containing all jobs
            use_min_max_scaling: Whether to use min-max scaling
            use_boolean_normalisation: Whether to use boolean normalisation
            use_tfidf_weighting: Whether to use TF-IDF style weighting
            importance_weights: Dictionary mapping skill categories to importance weights
        """
        self.skill_taxonomy = skill_taxonomy
        self.job_architecture = job_architecture
        
        # Load configuration values
        try:
            config_manager = get_config_manager()
            normalisation_config = config_manager.get_nested_value('data', 'normalisation', default={})
            
            # Use configuration values if not provided
            self.use_min_max_scaling = use_min_max_scaling if use_min_max_scaling is not None else normalisation_config.get('use_min_max_scaling', True)
            self.use_boolean_normalisation = use_boolean_normalisation if use_boolean_normalisation is not None else normalisation_config.get('use_boolean_normalisation', False)
            self.use_tfidf_weighting = use_tfidf_weighting if use_tfidf_weighting is not None else normalisation_config.get('use_tfidf_weighting', True)
        except Exception:
            # Fallback to defaults if configuration unavailable
            self.use_min_max_scaling = use_min_max_scaling if use_min_max_scaling is not None else True
            self.use_boolean_normalisation = use_boolean_normalisation if use_boolean_normalisation is not None else False
            self.use_tfidf_weighting = use_tfidf_weighting if use_tfidf_weighting is not None else True
        
        # Initialize normalisers
        self.min_max_scaler = MinMaxScaler()
        self.boolean_normaliser = BooleanNormaliser()
        self.tfidf_weighter = TfIdfWeighter(skill_taxonomy, job_architecture)
        self.category_weighter = CategoryWeighter(skill_taxonomy, importance_weights)
    
    def normalise_dict(self, proficiency_dict: Dict[str, int]) -> Dict[str, float]:
        """
        Apply all enabled normalisation strategies to a dictionary of skill proficiency values.
        
        Args:
            proficiency_dict: Dictionary mapping skill IDs to proficiency values
            
        Returns:
            Dictionary with normalised proficiency values
        """
        # Start with original proficiency values
        normalised_dict = dict(proficiency_dict)
        
        # Apply boolean normalisation if enabled
        if self.use_boolean_normalisation:
            normalised_dict = self.boolean_normaliser.normalise_dict(normalised_dict)
        # Apply min-max scaling if enabled (and not using boolean normalisation)
        elif self.use_min_max_scaling:
            normalised_dict = self.min_max_scaler.scale_dict(normalised_dict)
        
        # Apply TF-IDF weighting if enabled
        if self.use_tfidf_weighting:
            normalised_dict = self.tfidf_weighter.weight_dict(normalised_dict)
        
        # Apply category weighting
        normalised_dict = self.category_weighter.weight_dict(normalised_dict)
        
        return normalised_dict
    
    def normalise_job(self, job: Job) -> Dict[str, float]:
        """
        Normalise the skills of a job.
        
        Args:
            job: The job to normalise
            
        Returns:
            Dictionary with normalised skill proficiency values
        """
        return self.normalise_dict(job.skills)
    
    def normalise_employee(self, employee_skills: Dict[str, int]) -> Dict[str, float]:
        """
        Normalise the skills of an employee.
        
        Args:
            employee_skills: Dictionary mapping skill IDs to proficiency values
            
        Returns:
            Dictionary with normalised skill proficiency values
        """
        return self.normalise_dict(employee_skills)
