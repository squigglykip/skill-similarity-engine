"""
Corpus Normalizer Module

Handles corpus-wide normalization of similarity scores to preserve differentiation
while maintaining 0-1 range for interpretability. This is crucial for career pathway
intelligence where defining skills boosts can push scores above 1.0, and we want
to preserve the relative ranking and differentiation across all job pairs.

Key Features:
- Allows raw similarity scores to exceed 1.0 during calculation
- Normalizes entire corpus to 0-1 range after all calculations
- Preserves differentiation and ranking information
- Provides transparency through normalization statistics
- Supports both batch and incremental normalization approaches
"""

import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class NormalizationStats:
    """Statistics about the normalization process for transparency"""
    raw_min: float
    raw_max: float
    raw_mean: float
    raw_std: float
    normalization_factor: float
    total_scores: int
    scores_above_1: int
    percentage_above_1: float
    max_boost_observed: float


class CorpusNormalizer:
    """
    Handles corpus-wide normalization of similarity scores.
    
    This class collects raw enhanced similarity scores (which can exceed 1.0 due to
    defining skills boosts) and normalizes the entire corpus to a 0-1 range while
    preserving all differentiation and ranking information.
    
    Usage:
        normalizer = CorpusNormalizer()
        
        # Collect all raw scores
        for score in raw_scores:
            normalizer.collect_raw_score(score)
        
        # Normalize the corpus
        stats = normalizer.normalize_corpus()
        
        # Get normalized scores
        normalized = normalizer.get_normalized_score(raw_score)
    """
    
    def __init__(self):
        """Initialize the corpus normalizer."""
        self.logger = logging.getLogger(__name__)
        self.raw_scores: List[float] = []
        self.is_normalized = False
        self.normalization_stats: Optional[NormalizationStats] = None
        self._normalization_factor: Optional[float] = None
    
    def collect_raw_score(self, raw_enhanced_similarity: float) -> None:
        """
        Collect a raw similarity score for corpus normalization.
        
        Args:
            raw_enhanced_similarity: Raw enhanced similarity score (can be >1.0)
        """
        if self.is_normalized:
            raise ValueError("Cannot collect scores after normalization has been performed")
        
        if raw_enhanced_similarity < 0:
            self.logger.warning(f"Negative similarity score collected: {raw_enhanced_similarity}")
        
        self.raw_scores.append(raw_enhanced_similarity)
    
    def collect_raw_scores_batch(self, raw_scores: List[float]) -> None:
        """
        Collect multiple raw similarity scores at once.
        
        Args:
            raw_scores: List of raw enhanced similarity scores
        """
        for score in raw_scores:
            self.collect_raw_score(score)
    
    def normalize_corpus(self) -> NormalizationStats:
        """
        Normalize the entire corpus of similarity scores to 0-1 range.
        
        Uses max normalization to preserve all differentiation:
        normalized_score = raw_score / max(raw_scores)
        
        Returns:
            NormalizationStats with detailed information about the normalization
        """
        if len(self.raw_scores) == 0:
            raise ValueError("No scores collected for normalization")
        
        if self.is_normalized:
            self.logger.warning("Corpus already normalized, returning existing stats")
            return self.normalization_stats
        
        # Convert to numpy array for efficient computation
        raw_array = np.array(self.raw_scores)
        
        # Calculate normalization factor (max value)
        self._normalization_factor = float(np.max(raw_array))
        
        if self._normalization_factor == 0:
            self.logger.warning("Maximum similarity score is 0, normalization factor set to 1")
            self._normalization_factor = 1.0
        
        # Calculate statistics
        raw_min = float(np.min(raw_array))
        raw_max = float(np.max(raw_array))
        raw_mean = float(np.mean(raw_array))
        raw_std = float(np.std(raw_array))
        
        # Count scores above 1.0 (indicating defining skills boost impact)
        scores_above_1 = int(np.sum(raw_array > 1.0))
        percentage_above_1 = (scores_above_1 / len(self.raw_scores)) * 100
        max_boost_observed = raw_max - 1.0 if raw_max > 1.0 else 0.0
        
        # Create normalization stats
        self.normalization_stats = NormalizationStats(
            raw_min=raw_min,
            raw_max=raw_max,
            raw_mean=raw_mean,
            raw_std=raw_std,
            normalization_factor=self._normalization_factor,
            total_scores=len(self.raw_scores),
            scores_above_1=scores_above_1,
            percentage_above_1=percentage_above_1,
            max_boost_observed=max_boost_observed
        )
        
        self.is_normalized = True
        
        # Log normalization summary
        self.logger.info(f"Corpus normalization complete:")
        self.logger.info(f"  Total scores: {len(self.raw_scores):,}")
        self.logger.info(f"  Raw range: {raw_min:.4f} - {raw_max:.4f}")
        self.logger.info(f"  Normalization factor: {self._normalization_factor:.4f}")
        self.logger.info(f"  Scores above 1.0: {scores_above_1:,} ({percentage_above_1:.1f}%)")
        self.logger.info(f"  Max boost observed: {max_boost_observed:.4f}")
        
        return self.normalization_stats
    
    def get_normalized_score(self, raw_score: float) -> float:
        """
        Get the normalized version of a specific raw score.
        
        Args:
            raw_score: Raw enhanced similarity score
            
        Returns:
            Normalized score in 0-1 range
        """
        if not self.is_normalized:
            raise ValueError("Must call normalize_corpus() before getting normalized scores")
        
        if self._normalization_factor is None or self._normalization_factor == 0:
            return 0.0
        
        normalized = raw_score / self._normalization_factor
        
        # Ensure result is in valid range (handle floating point precision)
        return max(0.0, min(1.0, normalized))
    
    def get_normalized_scores_batch(self, raw_scores: List[float]) -> List[float]:
        """
        Get normalized versions of multiple raw scores.
        
        Args:
            raw_scores: List of raw enhanced similarity scores
            
        Returns:
            List of normalized scores in 0-1 range
        """
        return [self.get_normalized_score(score) for score in raw_scores]
    
    def get_normalization_stats(self) -> Optional[NormalizationStats]:
        """
        Get detailed statistics about the normalization process.
        
        Returns:
            NormalizationStats if normalization has been performed, None otherwise
        """
        return self.normalization_stats
    
    def get_normalization_factor(self) -> Optional[float]:
        """
        Get the normalization factor used to scale scores.
        
        Returns:
            Normalization factor (max raw score) if available, None otherwise
        """
        return self._normalization_factor
    
    def reset(self) -> None:
        """
        Reset the normalizer to collect a new corpus of scores.
        
        Warning: This clears all collected scores and normalization state.
        """
        self.raw_scores.clear()
        self.is_normalized = False
        self.normalization_stats = None
        self._normalization_factor = None
        self.logger.info("Corpus normalizer reset - ready for new score collection")
    
    def get_corpus_summary(self) -> Dict[str, Any]:
        """
        Get a comprehensive summary of the corpus and normalization.
        
        Returns:
            Dictionary with corpus statistics and normalization info
        """
        if not self.is_normalized:
            # Pre-normalization summary
            if len(self.raw_scores) == 0:
                return {"status": "no_scores_collected"}
            
            raw_array = np.array(self.raw_scores)
            return {
                "status": "scores_collected_not_normalized",
                "total_scores": len(self.raw_scores),
                "raw_min": float(np.min(raw_array)),
                "raw_max": float(np.max(raw_array)),
                "raw_mean": float(np.mean(raw_array)),
                "scores_above_1": int(np.sum(raw_array > 1.0)),
                "percentage_above_1": (int(np.sum(raw_array > 1.0)) / len(self.raw_scores)) * 100
            }
        
        # Post-normalization summary
        stats = self.normalization_stats
        return {
            "status": "normalized",
            "total_scores": stats.total_scores,
            "raw_range": f"{stats.raw_min:.4f} - {stats.raw_max:.4f}",
            "normalized_range": "0.0000 - 1.0000",
            "normalization_factor": stats.normalization_factor,
            "raw_mean": stats.raw_mean,
            "raw_std": stats.raw_std,
            "scores_above_1": stats.scores_above_1,
            "percentage_above_1": stats.percentage_above_1,
            "max_boost_observed": stats.max_boost_observed,
            "differentiation_preserved": True
        }


def create_corpus_normalizer() -> CorpusNormalizer:
    """
    Factory function to create a new corpus normalizer instance.
    
    Returns:
        New CorpusNormalizer instance ready for score collection
    """
    return CorpusNormalizer()


def normalize_similarity_corpus(raw_scores: List[float]) -> Tuple[List[float], NormalizationStats]:
    """
    Convenience function to normalize a complete corpus of similarity scores.
    
    Args:
        raw_scores: List of raw enhanced similarity scores
        
    Returns:
        Tuple of (normalized_scores, normalization_stats)
    """
    normalizer = CorpusNormalizer()
    normalizer.collect_raw_scores_batch(raw_scores)
    stats = normalizer.normalize_corpus()
    normalized_scores = normalizer.get_normalized_scores_batch(raw_scores)
    
    return normalized_scores, stats