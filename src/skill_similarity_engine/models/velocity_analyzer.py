#!/usr/bin/env python3
"""
Skill Velocity Analysis Engine
==============================

Temporal skill trend analysis system that calculates multi-timeframe CAGR
(Compound Annual Growth Rate) and categorizes skills by velocity patterns.

This module provides strategic intelligence on skill demand evolution,
identifying accelerating, growing, stable, and declining skills across
different time horizons for workforce planning.

Key Components:
- SkillVelocityAnalyzer: Main orchestrator for velocity calculations
- VelocityCalculator: CAGR and trend calculation logic
- VelocityCategorizor: Classification into growth categories
- TemporalAnalyzer: Multi-timeframe velocity analysis

Philosophy: Data-driven skill trend intelligence for strategic planning
"""

import pandas as pd
import numpy as np
import sqlite3
import warnings
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Union
from collections import defaultdict
from dataclasses import dataclass

# SSE Integration
from ..config.architectural_config_manager import get_config_manager
from ..error_handling.core import EngineError, ErrorCategory, ErrorSeverity
import logging

warnings.filterwarnings('ignore')

# Simple logging helper
logger = logging.getLogger(__name__)

def log_info(message: str, context_dict=None, **context):
    """Simple logging helper - disabled for cleaner output."""
    # Disabled for cleaner user experience
    pass


@dataclass
class VelocityResult:
    """Container for skill velocity analysis results."""
    velocity_df: pd.DataFrame
    velocity_summary: Dict[str, Any]
    temporal_trends: Dict[str, Any]


class VelocityCalculator:
    """
    CAGR and trend calculation engine for skill demand analysis.
    
    Calculates compound annual growth rates across multiple timeframes
    and provides statistical trend analysis for skill demand patterns.
    """
    
    def __init__(self):
        """Initialize velocity calculator."""
        log_info("VelocityCalculator initialized", {})
    
    def calculate_cagr(self, initial_value: float, final_value: float, 
                      time_periods: float) -> float:
        """
        Calculate Compound Annual Growth Rate (CAGR).
        
        Args:
            initial_value: Starting value
            final_value: Ending value
            time_periods: Number of time periods (years)
            
        Returns:
            CAGR as a decimal (e.g., 0.15 for 15% growth)
        """
        if initial_value <= 0 or time_periods <= 0:
            return 0.0
        
        try:
            cagr = (final_value / initial_value) ** (1 / time_periods) - 1
            return cagr
        except (ZeroDivisionError, ValueError, OverflowError):
            return 0.0
    
    def calculate_multi_timeframe_cagr(self, skill_timeline: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate CAGR across multiple timeframes for a skill.
        
        Args:
            skill_timeline: DataFrame with columns ['period', 'demand_count']
            
        Returns:
            Dictionary with short_term, medium_term, and long_term CAGR values
        """
        if len(skill_timeline) < 2:
            return {
                'short_term_cagr': 0.0,
                'medium_term_cagr': 0.0,
                'long_term_cagr': 0.0
            }
        
        # Sort by period
        timeline = skill_timeline.sort_values('period')
        
        # Calculate CAGRs for different timeframes
        cagrs = {}
        timeframes = {
            'short_term_cagr': 1,   # 1 year
            'medium_term_cagr': 2,  # 2 years
            'long_term_cagr': 3     # 3 years
        }
        
        for cagr_name, years in timeframes.items():
            if len(timeline) >= years + 1:
                # Use data points that are 'years' apart
                initial_idx = max(0, len(timeline) - years - 1)
                final_idx = len(timeline) - 1
                
                initial_value = timeline.iloc[initial_idx]['demand_count']
                final_value = timeline.iloc[final_idx]['demand_count']
                
                cagrs[cagr_name] = self.calculate_cagr(initial_value, final_value, years)
            else:
                cagrs[cagr_name] = 0.0
        
        return cagrs
    
    def calculate_recency_weighted_growth(self, skill_timeline: pd.DataFrame) -> Tuple[float, float]:
        """
        Calculate recency-weighted growth metrics.
        
        Args:
            skill_timeline: DataFrame with columns ['period', 'demand_count']
            
        Returns:
            Tuple of (total_recency_weighted_movements, recency_weighted_growth_pct)
        """
        if len(skill_timeline) < 2:
            return 0.0, 0.0
        
        timeline = skill_timeline.sort_values('period')
        
        # Apply exponential decay weighting (more recent = higher weight)
        decay_rate = 0.1  # Configurable decay rate
        weights = np.exp(-decay_rate * np.arange(len(timeline))[::-1])
        
        # Calculate weighted movements
        weighted_movements = np.sum(timeline['demand_count'] * weights)
        
        # Calculate weighted growth percentage
        if len(timeline) >= 2:
            initial_weighted = timeline.iloc[0]['demand_count'] * weights[0]
            final_weighted = timeline.iloc[-1]['demand_count'] * weights[-1]
            
            if initial_weighted > 0:
                growth_pct = ((final_weighted - initial_weighted) / initial_weighted) * 100
            else:
                growth_pct = 0.0
        else:
            growth_pct = 0.0
        
        return weighted_movements, growth_pct


class VelocityCategorizor:
    """
    Classification engine for skill velocity patterns.
    
    Categorizes skills into velocity categories (accelerating, growing, stable, declining)
    based on CAGR thresholds and trend consistency.
    """
    
    def __init__(self, config_manager=None):
        """Initialize velocity categorizor with configuration."""
        self.config_manager = config_manager or get_config_manager()
        self.velocity_config = self._load_velocity_config()
        
        # Load categorization thresholds
        cat_config = self.velocity_config.get('categorization', {})
        self.accelerating_threshold = cat_config.get('accelerating_threshold', 0.2)
        self.growing_threshold = cat_config.get('growing_threshold', 0.05)
        self.declining_threshold = cat_config.get('declining_threshold', -0.05)
        
        log_info("VelocityCategorizor initialized", {
            'accelerating_threshold': self.accelerating_threshold,
            'growing_threshold': self.growing_threshold,
            'declining_threshold': self.declining_threshold
        })
    
    def _load_velocity_config(self) -> Dict[str, Any]:
        """Load velocity analysis configuration."""
        try:
            velocity_config = self.config_manager.get_nested_value(
                'core', 'clustering_analysis', 'velocity_analysis'
            )
            
            if velocity_config:
                return velocity_config
            
            # Fallback to default configuration
            return self._get_default_velocity_config()
            
        except Exception as e:
            log_info("Failed to load velocity config, using defaults", {
                'error': str(e)
            })
            return self._get_default_velocity_config()
    
    def _get_default_velocity_config(self) -> Dict[str, Any]:
        """Get default velocity analysis configuration."""
        return {
            'timeframes': {
                'short_term': 1,
                'medium_term': 2,
                'long_term': 3
            },
            'categorization': {
                'accelerating_threshold': 0.2,
                'growing_threshold': 0.05,
                'declining_threshold': -0.05
            }
        }
    
    def categorize_velocity(self, short_term_cagr: float, medium_term_cagr: float, 
                          long_term_cagr: float) -> Tuple[str, str]:
        """
        Categorize skill velocity based on CAGR values.
        
        Args:
            short_term_cagr: 1-year CAGR
            medium_term_cagr: 2-year CAGR
            long_term_cagr: 3-year CAGR
            
        Returns:
            Tuple of (velocity_category, trend_direction)
        """
        # Calculate average CAGR for primary categorization
        cagrs = [short_term_cagr, medium_term_cagr, long_term_cagr]
        valid_cagrs = [c for c in cagrs if not np.isnan(c) and c != 0]
        
        if not valid_cagrs:
            return 'stable', 'stable'
        
        avg_cagr = np.mean(valid_cagrs)
        
        # Determine velocity category
        if avg_cagr >= self.accelerating_threshold:
            velocity_category = 'accelerating'
        elif avg_cagr >= self.growing_threshold:
            velocity_category = 'growing'
        elif avg_cagr <= self.declining_threshold:
            velocity_category = 'declining'
        else:
            velocity_category = 'stable'
        
        # Determine trend direction based on recent vs. long-term
        if short_term_cagr > long_term_cagr:
            trend_direction = 'up'
        elif short_term_cagr < long_term_cagr:
            trend_direction = 'down'
        else:
            trend_direction = 'stable'
        
        return velocity_category, trend_direction
    
    def assess_trend_consistency(self, short_term_cagr: float, medium_term_cagr: float, 
                               long_term_cagr: float) -> float:
        """
        Assess consistency of trend across timeframes.
        
        Args:
            short_term_cagr: 1-year CAGR
            medium_term_cagr: 2-year CAGR
            long_term_cagr: 3-year CAGR
            
        Returns:
            Consistency score (0-1, higher = more consistent)
        """
        cagrs = [short_term_cagr, medium_term_cagr, long_term_cagr]
        valid_cagrs = [c for c in cagrs if not np.isnan(c) and c != 0]
        
        if len(valid_cagrs) < 2:
            return 0.0
        
        # Calculate coefficient of variation (inverse of consistency)
        std_dev = np.std(valid_cagrs)
        mean_cagr = np.mean(valid_cagrs)
        
        if mean_cagr == 0:
            return 0.0
        
        cv = abs(std_dev / mean_cagr)
        consistency = float(max(0, 1 - cv))  # Higher consistency = lower coefficient of variation
        
        return consistency


class TemporalAnalyzer:
    """
    Multi-timeframe temporal analysis for skill demand patterns.
    
    Analyzes skill demand evolution across different time horizons
    and provides strategic insights on temporal trends.
    """
    
    def __init__(self, config_manager=None):
        """Initialize temporal analyzer."""
        self.config_manager = config_manager or get_config_manager()
        self.velocity_config = self._load_velocity_config()
        
        # Load timeframe configuration
        timeframe_config = self.velocity_config.get('timeframes', {})
        self.short_term_years = timeframe_config.get('short_term', 1)
        self.medium_term_years = timeframe_config.get('medium_term', 2)
        self.long_term_years = timeframe_config.get('long_term', 3)
        
        # Initialize shared calculator and categorizer instances
        self.calculator = VelocityCalculator()
        self.categorizor = VelocityCategorizor(config_manager)
        
        log_info("TemporalAnalyzer initialized", {
            'short_term_years': self.short_term_years,
            'medium_term_years': self.medium_term_years,
            'long_term_years': self.long_term_years
        })
    
    def _load_velocity_config(self) -> Dict[str, Any]:
        """Load velocity configuration."""
        try:
            velocity_config = self.config_manager.get_nested_value(
                'core', 'clustering_analysis', 'velocity_analysis'
            )
            
            if velocity_config:
                return velocity_config
            
            # Fallback to default configuration
            return self._get_default_velocity_config()
            
        except Exception as e:
            log_info("Failed to load velocity config, using defaults", {
                'error': str(e)
            })
            return self._get_default_velocity_config()
    
    def _get_default_velocity_config(self) -> Dict[str, Any]:
        """Get default velocity analysis configuration."""
        return {
            'timeframes': {
                'short_term': 1,
                'medium_term': 2,
                'long_term': 3
            },
            'categorization': {
                'accelerating_threshold': 0.2,
                'growing_threshold': 0.05,
                'declining_threshold': -0.05
            }
        }
    
    def analyze_skill_timeline(self, db_path: str, skill_id: str) -> Dict[str, Any]:
        """
        Analyze temporal patterns for a specific skill.
        
        Args:
            db_path: Path to the SQLite database
            skill_id: ID of the skill to analyze
            
        Returns:
            Dictionary with temporal analysis results
        """
        try:
            with sqlite3.connect(db_path) as conn:
                # Query skill demand over time using analytics_movement_patterns
                timeline_query = """
                SELECT 
                    SUBSTR(mp.movement_month, 1, 4) as year,
                    SUM(mp.movement_count) as demand_count
                FROM analytics_movement_patterns mp
                JOIN core_job_skill_requirements js ON mp.to_job_profile_id = js.JobProfileID
                WHERE js.Skill_ID = ?
                  AND mp.movement_month IS NOT NULL
                  AND mp.to_job_profile_id IS NOT NULL
                GROUP BY SUBSTR(mp.movement_month, 1, 4)
                ORDER BY year
                """
                
                timeline_df = pd.read_sql_query(timeline_query, conn, params=[skill_id])
                
                if len(timeline_df) == 0:
                    return {'error': 'No timeline data found for skill'}
                
                # Convert year to numeric and rename for consistency
                timeline_df['period'] = pd.to_numeric(timeline_df['year'])
                timeline_df = timeline_df[['period', 'demand_count']].copy()
                
                # Calculate velocity metrics using shared instances
                cagrs = self.calculator.calculate_multi_timeframe_cagr(timeline_df)
                weighted_movements, weighted_growth = self.calculator.calculate_recency_weighted_growth(timeline_df)
                
                # Categorize velocity using shared instance
                velocity_category, trend_direction = self.categorizor.categorize_velocity(
                    cagrs['short_term_cagr'], 
                    cagrs['medium_term_cagr'], 
                    cagrs['long_term_cagr']
                )
                
                consistency = self.categorizor.assess_trend_consistency(
                    cagrs['short_term_cagr'], 
                    cagrs['medium_term_cagr'], 
                    cagrs['long_term_cagr']
                )
                
                return {
                    'skill_id': skill_id,
                    'timeline_data': timeline_df.to_dict('records'),
                    'cagr_metrics': cagrs,
                    'velocity_category': velocity_category,
                    'trend_direction': trend_direction,
                    'trend_consistency': consistency,
                    'total_movements': timeline_df['demand_count'].sum(),
                    'recency_weighted_movements': weighted_movements,
                    'recency_weighted_growth_pct': weighted_growth,
                    'analysis_period': f"{timeline_df['period'].min()}-{timeline_df['period'].max()}"
                }
                
        except Exception as e:
            log_info("Failed to analyze skill timeline", {
                'skill_id': skill_id, 'error': str(e)
            })
            return {'error': str(e)}


class SkillVelocityAnalyzer:
    """
    Main orchestrator for skill velocity analysis.
    
    Coordinates temporal analysis, CAGR calculations, and velocity categorization
    to produce comprehensive skill demand intelligence for strategic planning.
    """
    
    def __init__(self, config_manager=None):
        """Initialize skill velocity analyzer."""
        self.config_manager = config_manager or get_config_manager()
        self.calculator = VelocityCalculator()
        self.categorizor = VelocityCategorizor(config_manager)
        self.temporal_analyzer = TemporalAnalyzer(config_manager)
        
        log_info("SkillVelocityAnalyzer initialized", {})
    
    def analyze_all_skills_velocity(self, db_path: str) -> VelocityResult:
        """
        Perform velocity analysis for all skills in the database.
        
        Args:
            db_path: Path to the SQLite database
            
        Returns:
            VelocityResult with comprehensive velocity analysis
        """
        log_info("Starting comprehensive skill velocity analysis", {
            'database': db_path
        })
        
        try:
            # Load all skills with demand data
            skills_data = self._load_skills_for_velocity_analysis(db_path)
            
            if skills_data is None or len(skills_data) == 0:
                raise ValueError("No skills data available for velocity analysis")
            
            # Analyze velocity for each skill
            velocity_results = []
            
            for _, skill in skills_data.iterrows():
                skill_analysis = self.temporal_analyzer.analyze_skill_timeline(
                    db_path, skill['skill_id']
                )
                
                if 'error' not in skill_analysis:
                    # Combine skill metadata with velocity analysis
                    velocity_record = {
                        'skill_id': skill['skill_id'],
                        'skill_name': skill['skill_name'],
                        'category': skill['category'],
                        'skill_type': skill['skill_type'],
                        'jobs_requiring_skill': skill['jobs_count'],
                        'total_skill_instances': skill['total_occurrences'],
                        'short_term_cagr': skill_analysis['cagr_metrics']['short_term_cagr'],
                        'medium_term_cagr': skill_analysis['cagr_metrics']['medium_term_cagr'],
                        'long_term_cagr': skill_analysis['cagr_metrics']['long_term_cagr'],
                        'velocity_category': skill_analysis['velocity_category'],
                        'trend_direction': skill_analysis['trend_direction'],
                        'total_movements': skill_analysis['total_movements'],
                        'total_recency_weighted_movements': skill_analysis['recency_weighted_movements'],
                        'recency_weighted_growth_pct': skill_analysis['recency_weighted_growth_pct'],
                        'created_timestamp': datetime.now().isoformat()
                    }
                    
                    velocity_results.append(velocity_record)
            
            # Create velocity DataFrame
            velocity_df = pd.DataFrame(velocity_results)
            
            # Generate summary statistics
            velocity_summary = self._generate_velocity_summary(velocity_df)
            
            # Generate temporal trends analysis
            temporal_trends = self._analyze_temporal_trends(velocity_df)
            
            result = VelocityResult(
                velocity_df=velocity_df,
                velocity_summary=velocity_summary,
                temporal_trends=temporal_trends
            )
            
            log_info("Skill velocity analysis completed", {
                'total_skills_analyzed': len(velocity_df),
                'accelerating_skills': len(velocity_df[velocity_df['velocity_category'] == 'accelerating']),
                'growing_skills': len(velocity_df[velocity_df['velocity_category'] == 'growing']),
                'declining_skills': len(velocity_df[velocity_df['velocity_category'] == 'declining'])
            })
            
            return result
            
        except Exception as e:
            log_info("Skill velocity analysis failed", {
                'error': str(e)
            })
            raise
    
    def _load_skills_for_velocity_analysis(self, db_path: str) -> Optional[pd.DataFrame]:
        """Load skills data suitable for velocity analysis."""
        try:
            with sqlite3.connect(db_path) as conn:
                skills_query = """
                SELECT 
                    s.Skill_ID as skill_id,
                    s.Skill_Name as skill_name,
                    s.Category as category,
                    s.SkillType as skill_type,
                    COUNT(DISTINCT js.JobProfileID) as jobs_count,
                    COUNT(*) as total_occurrences,
                    MIN(mp.movement_month) as earliest_date,
                    MAX(mp.movement_month) as latest_date
                FROM core_skills_taxonomy s
                JOIN core_job_skill_requirements js ON s.Skill_ID = js.Skill_ID
                JOIN analytics_movement_patterns mp ON js.JobProfileID = mp.to_job_profile_id
                WHERE mp.movement_month IS NOT NULL
                  AND mp.to_job_profile_id IS NOT NULL
                GROUP BY s.Skill_ID, s.Skill_Name, s.Category, s.SkillType
                HAVING jobs_count >= 3  -- Only skills with reasonable demand
                   AND earliest_date != latest_date  -- Only skills with temporal variation
                ORDER BY jobs_count DESC
                """
                
                skills_df = pd.read_sql_query(skills_query, conn)
                
                if len(skills_df) == 0:
                    log_info("No skills found suitable for velocity analysis", {})
                    return None
                
                log_info("Loaded skills for velocity analysis", {
                    'total_skills': len(skills_df),
                    'avg_jobs_per_skill': skills_df['jobs_count'].mean(),
                    'date_range': f"{skills_df['earliest_date'].min()} to {skills_df['latest_date'].max()}"
                })
                
                return skills_df
                
        except Exception as e:
            log_info("Failed to load skills for velocity analysis", {
                'error': str(e)
            })
            return None
    
    def _generate_velocity_summary(self, velocity_df: pd.DataFrame) -> Dict[str, Any]:
        """Generate summary statistics for velocity analysis."""
        if len(velocity_df) == 0:
            return {}
        
        # Category distribution
        category_counts = velocity_df['velocity_category'].value_counts().to_dict()
        
        # Trend direction distribution
        trend_counts = velocity_df['trend_direction'].value_counts().to_dict()
        
        # CAGR statistics
        cagr_stats = {
            'short_term': {
                'mean': velocity_df['short_term_cagr'].mean(),
                'median': velocity_df['short_term_cagr'].median(),
                'std': velocity_df['short_term_cagr'].std()
            },
            'medium_term': {
                'mean': velocity_df['medium_term_cagr'].mean(),
                'median': velocity_df['medium_term_cagr'].median(),
                'std': velocity_df['medium_term_cagr'].std()
            },
            'long_term': {
                'mean': velocity_df['long_term_cagr'].mean(),
                'median': velocity_df['long_term_cagr'].median(),
                'std': velocity_df['long_term_cagr'].std()
            }
        }
        
        # Top accelerating and declining skills
        top_accelerating = velocity_df.nlargest(10, 'short_term_cagr')[['skill_name', 'short_term_cagr']].to_dict('records')
        top_declining = velocity_df.nsmallest(10, 'short_term_cagr')[['skill_name', 'short_term_cagr']].to_dict('records')
        
        return {
            'total_skills_analyzed': len(velocity_df),
            'velocity_categories': category_counts,
            'trend_directions': trend_counts,
            'cagr_statistics': cagr_stats,
            'top_accelerating_skills': top_accelerating,
            'top_declining_skills': top_declining,
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def _analyze_temporal_trends(self, velocity_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze temporal trends across all skills."""
        if len(velocity_df) == 0:
            return {}
        
        # Correlation between timeframes
        correlations = {}
        if len(velocity_df) > 1:
            correlations = {
                'short_medium': velocity_df['short_term_cagr'].corr(velocity_df['medium_term_cagr']),
                'short_long': velocity_df['short_term_cagr'].corr(velocity_df['long_term_cagr']),
                'medium_long': velocity_df['medium_term_cagr'].corr(velocity_df['long_term_cagr'])
            }
        
        # Category-based trends
        category_trends = {}
        for category in velocity_df['category'].unique():
            cat_data = velocity_df[velocity_df['category'] == category]
            category_trends[category] = {
                'count': len(cat_data),
                'avg_short_term_cagr': cat_data['short_term_cagr'].mean(),
                'avg_medium_term_cagr': cat_data['medium_term_cagr'].mean(),
                'avg_long_term_cagr': cat_data['long_term_cagr'].mean(),
                'velocity_distribution': cat_data['velocity_category'].value_counts().to_dict()
            }
        
        return {
            'timeframe_correlations': correlations,
            'category_trends': category_trends,
            'overall_trend_direction': velocity_df['trend_direction'].mode().iloc[0] if len(velocity_df) > 0 else 'stable',
            'trend_consistency': {
                'high_consistency_skills': len(velocity_df[
                    (velocity_df['short_term_cagr'] > 0) & 
                    (velocity_df['medium_term_cagr'] > 0) & 
                    (velocity_df['long_term_cagr'] > 0)
                ]),
                'mixed_trend_skills': len(velocity_df[
                    ((velocity_df['short_term_cagr'] > 0) & (velocity_df['long_term_cagr'] < 0)) |
                    ((velocity_df['short_term_cagr'] < 0) & (velocity_df['long_term_cagr'] > 0))
                ])
            }
        }