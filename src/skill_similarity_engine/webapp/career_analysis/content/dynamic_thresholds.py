"""
Dynamic similarity threshold calculation based on actual data distribution.
Implements percentile-based classification that adapts to real similarity patterns.
"""

from typing import Dict, List, Tuple, Optional
import sqlite3
from dataclasses import dataclass
import numpy as np

@dataclass
class PercentileThreshold:
    """Represents a percentile-based threshold range."""
    percentile_min: float
    percentile_max: float
    similarity_min: float
    similarity_max: float
    content_key: str
    descriptor: str
    quality_level: str

class DynamicSimilarityThresholds:
    """Calculates dynamic similarity thresholds based on actual data distribution."""
    
    def __init__(self, db_connection):
        self.db = db_connection
        self._similarity_distribution = None
        self._percentile_thresholds = None
        self._cache_valid = False
    
    def get_similarity_distribution(self, refresh_cache: bool = False) -> Dict:
        """Get similarity score distribution from database."""
        if self._similarity_distribution is None or refresh_cache:
            self._calculate_similarity_distribution()
        return self._similarity_distribution
    
    def _calculate_similarity_distribution(self):
        """Calculate similarity distribution statistics from database."""
        try:
            # Get all similarity scores
            query = """
            SELECT similarity_score 
            FROM job_similarities 
            WHERE similarity_score > 0.0 AND similarity_score < 1.0
            ORDER BY similarity_score
            """
            cursor = self.db.execute(query)
            scores = [row[0] for row in cursor.fetchall()]
            
            if not scores:
                # Fallback to default distribution
                self._similarity_distribution = self._get_default_distribution()
                return
            
            # Calculate percentiles
            percentiles = [5, 10, 25, 50, 75, 90, 95]
            percentile_values = np.percentile(scores, percentiles)
            
            self._similarity_distribution = {
                'total_scores': len(scores),
                'mean': np.mean(scores),
                'median': np.median(scores),
                'std': np.std(scores),
                'min': min(scores),
                'max': max(scores),
                'percentiles': {
                    p: percentile_values[i] for i, p in enumerate(percentiles)
                },
                'raw_scores': scores  # For detailed analysis
            }
            
            # Calculate dynamic thresholds
            self._calculate_dynamic_thresholds()
            
            print(f"ðŸ“Š Similarity Distribution Analysis:")
            print(f"   â€¢ Total similarity pairs: {len(scores):,}")
            print(f"   â€¢ Mean similarity: {np.mean(scores):.3f}")
            print(f"   â€¢ Median similarity: {np.median(scores):.3f}")
            print(f"   â€¢ 95th percentile: {percentile_values[-1]:.3f}")
            print(f"   â€¢ 90th percentile: {percentile_values[-2]:.3f}")
            print(f"   â€¢ 75th percentile: {percentile_values[-3]:.3f}")
            
        except Exception as e:
            print(f"âš ï¸ Error calculating similarity distribution: {e}")
            self._similarity_distribution = self._get_default_distribution()
    
    def _calculate_dynamic_thresholds(self):
        """Calculate dynamic thresholds based on percentile distribution."""
        percentiles = self._similarity_distribution['percentiles']
        
        # Define percentile-based thresholds
        self._percentile_thresholds = [
            PercentileThreshold(
                percentile_min=95, percentile_max=100,
                similarity_min=percentiles[95], similarity_max=1.0,
                content_key="outstanding_opportunities", 
                descriptor="Outstanding",
                quality_level="Immediate transition ready"
            ),
            PercentileThreshold(
                percentile_min=90, percentile_max=95,
                similarity_min=percentiles[90], similarity_max=percentiles[95],
                content_key="excellent_opportunities",
                descriptor="Excellent", 
                quality_level="Smooth transition prospects"
            ),
            PercentileThreshold(
                percentile_min=75, percentile_max=90,
                similarity_min=percentiles[75], similarity_max=percentiles[90],
                content_key="good_opportunities",
                descriptor="Good",
                quality_level="Manageable development required"
            ),
            PercentileThreshold(
                percentile_min=50, percentile_max=75,
                similarity_min=percentiles[50], similarity_max=percentiles[75],
                content_key="development_opportunities",
                descriptor="Development Required",
                quality_level="Significant upskilling needed"
            ),
            PercentileThreshold(
                percentile_min=0, percentile_max=50,
                similarity_min=0.0, similarity_max=percentiles[50],
                content_key="transformation_required",
                descriptor="Transformation Required",
                quality_level="Major career pivot required"
            )
        ]
    
    def get_narrative_type(self, similarity_score: float) -> str:
        """Determine narrative type based on dynamic percentile thresholds."""
        if self._percentile_thresholds is None:
            self.get_similarity_distribution()  # Initialize if needed
        
        for threshold in self._percentile_thresholds:
            if threshold.similarity_min <= similarity_score <= threshold.similarity_max:
                return threshold.content_key
        
        return "transformation_required"  # fallback
    
    def get_similarity_context(self, similarity_score: float) -> Dict:
        """Get comprehensive context for a similarity score."""
        if self._percentile_thresholds is None:
            self.get_similarity_distribution()
        
        # Find matching threshold
        for threshold in self._percentile_thresholds:
            if threshold.similarity_min <= similarity_score <= threshold.similarity_max:
                # Calculate actual percentile rank
                scores = self._similarity_distribution['raw_scores']
                percentile_rank = (sum(1 for s in scores if s <= similarity_score) / len(scores)) * 100
                
                return {
                    'narrative_type': threshold.content_key,
                    'descriptor': threshold.descriptor,
                    'quality_level': threshold.quality_level,
                    'percentile_rank': percentile_rank,
                    'percentile_range': f"{threshold.percentile_min}th-{threshold.percentile_max}th",
                    'similarity_score': similarity_score,
                    'distribution_context': {
                        'vs_mean': similarity_score - self._similarity_distribution['mean'],
                        'vs_median': similarity_score - self._similarity_distribution['median'],
                        'standard_deviations': (similarity_score - self._similarity_distribution['mean']) / self._similarity_distribution['std']
                    }
                }
        
        # Fallback context
        return {
            'narrative_type': 'transformation_required',
            'descriptor': 'Transformation Required',
            'quality_level': 'Major career pivot required',
            'percentile_rank': 0,
            'percentile_range': 'Below median',
            'similarity_score': similarity_score
        }
    
    def get_threshold_summary(self) -> Dict:
        """Get summary of current dynamic thresholds for debugging/display."""
        if self._percentile_thresholds is None:
            self.get_similarity_distribution()
        
        return {
            'distribution_stats': self._similarity_distribution,
            'thresholds': [
                {
                    'descriptor': t.descriptor,
                    'percentile_range': f"{t.percentile_min}-{t.percentile_max}%",
                    'similarity_range': f"{t.similarity_min:.3f}-{t.similarity_max:.3f}",
                    'content_key': t.content_key,
                    'quality_level': t.quality_level
                }
                for t in self._percentile_thresholds
            ]
        }
    
    def _get_default_distribution(self) -> Dict:
        """Fallback distribution if database query fails."""
        return {
            'total_scores': 0,
            'mean': 0.35,
            'median': 0.35,
            'std': 0.15,
            'min': 0.0,
            'max': 1.0,
            'percentiles': {
                5: 0.15,
                10: 0.20,
                25: 0.28,
                50: 0.35,
                75: 0.45,
                90: 0.55,
                95: 0.65
            },
            'raw_scores': []
        }

class AdaptiveContentSelector:
    """Selects content based on dynamic similarity thresholds and business context."""
    
    def __init__(self, db_connection):
        self.dynamic_thresholds = DynamicSimilarityThresholds(db_connection)
        self.db = db_connection
    
    def get_enhanced_analysis_context(self, similarity_score: float, job_from: str, 
                                    job_to: Optional[str] = None) -> Dict:
        """Get enhanced analysis context with dynamic thresholds and business intelligence."""
        
        # Get dynamic similarity context
        similarity_context = self.dynamic_thresholds.get_similarity_context(similarity_score)
        
        # Get business context
        business_context = self._get_business_context(job_from, job_to)
        
        # Combine contexts
        enhanced_context = {
            **similarity_context,
            **business_context,
            'analysis_approach': self._determine_analysis_approach(similarity_context, business_context),
            'confidence_factors': self._calculate_confidence_factors(similarity_context, business_context)
        }
        
        return enhanced_context
    
    def _get_business_context(self, job_from: str, job_to: Optional[str]) -> Dict:
        """Extract business context for jobs."""
        try:
            # Get source job context
            source_query = """
            SELECT j.JobProfile, j.Job, j.JobFunction, j.JobCategory, j.ManagementLevel,
                   COUNT(p."Position Number") as position_count,
                   GROUP_CONCAT(DISTINCT p.Division) as divisions,
                   GROUP_CONCAT(DISTINCT p.Location) as locations
            FROM jobs j
            LEFT JOIN positions p ON j.JobProfileID = p.JobProfileID
            WHERE j.JobProfileID = ?
            GROUP BY j.JobProfileID, j.JobProfile, j.Job, j.JobFunction, j.JobCategory, j.ManagementLevel
            """
            source_result = self.db.execute(source_query, (job_from,)).fetchone()
            
            business_context = {
                'source_job_context': dict(source_result) if source_result else {},
                'target_job_context': {},
                'cross_functional': False,
                'cross_divisional': False,
                'level_change': 'same'
            }
            
            if job_to:
                # Get target job context
                target_result = self.db.execute(source_query, (job_to,)).fetchone()
                if target_result:
                    business_context['target_job_context'] = dict(target_result)
                    
                    # Analyze transition characteristics
                    if source_result and target_result:
                        business_context['cross_functional'] = source_result['JobFunction'] != target_result['JobFunction']
                        business_context['cross_divisional'] = source_result['divisions'] != target_result['divisions']
                        
                        # Simplified level analysis using ManagementLevel
                        source_level = source_result['ManagementLevel'] or 'Group 1'
                        target_level = target_result['ManagementLevel'] or 'Group 1'
                        
                        # Extract numeric part from "Group X" format
                        try:
                            source_num = int(source_level.split()[-1]) if 'Group' in source_level else 1
                            target_num = int(target_level.split()[-1]) if 'Group' in target_level else 1
                            
                            if target_num > source_num:
                                business_context['level_change'] = 'promotion'
                            elif target_num < source_num:
                                business_context['level_change'] = 'lateral_down'
                            else:
                                business_context['level_change'] = 'lateral'
                        except:
                            business_context['level_change'] = 'lateral'
            
            return business_context
            
        except Exception as e:
            print(f"âš ï¸ Error getting business context: {e}")
            return {'source_job_context': {}, 'target_job_context': {}}
    
    def _determine_analysis_approach(self, similarity_context: Dict, business_context: Dict) -> str:
        """Determine the appropriate analysis approach based on context."""
        percentile_rank = similarity_context.get('percentile_rank', 0)
        
        if percentile_rank >= 95:
            return "accelerated_transition"
        elif percentile_rank >= 75:
            return "standard_transition"
        elif percentile_rank >= 50:
            return "development_focused"
        else:
            return "transformation_required"
    
    def _calculate_confidence_factors(self, similarity_context: Dict, business_context: Dict) -> List[str]:
        """Calculate factors that affect confidence in the analysis."""
        factors = []
        
        percentile_rank = similarity_context.get('percentile_rank', 0)
        
        if percentile_rank >= 90:
            factors.append("High similarity score (top 10%)")
        
        source_positions = business_context.get('source_job_context', {}).get('position_count', 0)
        if source_positions > 10:
            factors.append(f"Large workforce impact ({source_positions} positions)")
        elif source_positions > 0:
            factors.append(f"Moderate workforce impact ({source_positions} positions)")
        
        if business_context.get('cross_functional'):
            factors.append("Cross-functional transition complexity")
        
        if business_context.get('cross_divisional'):
            factors.append("Cross-divisional transition considerations")
        
        level_change = business_context.get('level_change', 'same')
        if level_change == 'promotion':
            factors.append("Career progression opportunity")
        elif level_change == 'lateral_down':
            factors.append("Level adjustment considerations")
        
        return factors 
