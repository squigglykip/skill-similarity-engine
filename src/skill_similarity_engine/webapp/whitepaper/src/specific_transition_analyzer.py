"""
Specific Transition Analyzer for NAB Skills Intelligence Platform

This module provides analysis capabilities for specific job-to-job transitions,
supporting both single target analysis and multiple target comparisons.
Uses the job_similarities table for comprehensive transition data.

Author: NAB Skills Intelligence Team
Created: 2025-01-19
"""

import sqlite3
import logging
from typing import Dict, List, Tuple, Optional, Any
from skill_similarity_engine.utils.display import JobDisplayManager, DisplayFormat

logger = logging.getLogger(__name__)

class SpecificTransitionAnalyzer:
    """
    Analyzer for specific job transition scenarios.
    
    Provides detailed analysis of transitions between specific jobs using the
    job_similarities table, supporting both single transitions and comparative
    analysis of multiple targets.
    """
    
    def __init__(self, db_connection: sqlite3.Connection):
        """
        Initialize the analyzer with database connection.
        
        Args:
            db_connection: SQLite database connection
        """
        self.db = db_connection
        self.job_display_manager = JobDisplayManager(db_connection)
        logger.info("SpecificTransitionAnalyzer initialized")
    
    def analyze_single_transition(self, job_from: str, job_to: str, 
                                similarity_range: Tuple[float, float] = (0.4, 0.9)) -> Dict[str, Any]:
        """
        Analyze a specific job-to-job transition using job_similarities table.
        
        Args:
            job_from: Source JobProfileID
            job_to: Target JobProfileID  
            similarity_range: (min_similarity, max_similarity) tuple (0.0-1.0 scale)
            
        Returns:
            Comprehensive analysis data for single transition including:
            - Transition metrics (similarity, skills overlap, difficulty)
            - Skills gap analysis 
            - Career move classification
            - Strategic context
        """
        logger.info(f"Analyzing single transition: {job_from} → {job_to}")
        
        # Get transition similarity data
        transition_data = self._get_transition_similarity(job_from, job_to)
        if not transition_data:
            raise ValueError(f"No similarity data found between {job_from} and {job_to}")
        
        # Get skills analysis
        skills_analysis = self._analyze_skills_gap(job_from, job_to)
        
        # Classify transition type
        move_classification = self._classify_career_move(job_from, job_to, transition_data['similarity_score'])
        
        # Get job context information
        source_context = self._get_job_context(job_from)
        target_context = self._get_job_context(job_to)
        
        # Build comprehensive analysis
        analysis = {
            'analysis_mode': 'specific_single',
            'source_job': {
                'job_id': job_from,
                'logical_display_name': self.job_display_manager.get_display_name(job_from, DisplayFormat.LOGICAL),
                'job_function': source_context.get('job_function'),
                'management_level': source_context.get('management_level')
            },
            'target_job': {
                'job_id': job_to,
                'logical_display_name': self.job_display_manager.get_display_name(job_to, DisplayFormat.LOGICAL),
                'job_function': target_context.get('job_function'),
                'management_level': target_context.get('management_level')
            },
            'transition_metrics': {
                'similarity_score': round(transition_data['similarity_score'] * 100, 1),
                'similarity_percentile': self._calculate_similarity_percentile(transition_data['similarity_score']),
                'skill_overlap_score': round((transition_data.get('skill_overlap_score') or 0) * 100, 1),
                'shared_skills_count': transition_data.get('shared_skills_count') or 0,
                'total_skills_from': transition_data.get('total_skills_from') or 0,
                'total_skills_to': transition_data.get('total_skills_to') or 0
            },
            'skills_analysis': skills_analysis,
            'move_classification': move_classification,
            'strategic_context': self._generate_strategic_context(
                source_context, target_context, transition_data, move_classification
            ),
            'within_similarity_range': self._check_similarity_range(
                transition_data['similarity_score'], similarity_range
            )
        }
        
        logger.info(f"Single transition analysis complete: {analysis['transition_metrics']['similarity_score']}% similarity")
        return analysis
    
    def analyze_multiple_transitions(self, job_from: str, job_to_list: List[str],
                                   similarity_range: Tuple[float, float] = (0.4, 0.9)) -> Dict[str, Any]:
        """
        Analyze multiple target transitions for comparative analysis.
        
        Args:
            job_from: Source JobProfileID
            job_to_list: List of target JobProfileIDs
            similarity_range: (min_similarity, max_similarity) tuple
            
        Returns:
            Ranked comparison data structure with:
            - Individual transition analyses
            - Comparative rankings
            - Strategic recommendations for portfolio approach
        """
        logger.info(f"Analyzing multiple transitions from {job_from} to {len(job_to_list)} targets")
        
        # Analyze each individual transition
        individual_analyses = []
        for job_to in job_to_list:
            try:
                analysis = self.analyze_single_transition(job_from, job_to, similarity_range)
                individual_analyses.append(analysis)
            except ValueError as e:
                logger.warning(f"Skipping {job_to}: {e}")
                continue
        
        if not individual_analyses:
            raise ValueError("No valid transitions found in target list")
        
        # Sort by similarity score (descending)
        individual_analyses.sort(
            key=lambda x: x['transition_metrics']['similarity_score'], 
            reverse=True
        )
        
        # Generate comparative analysis
        comparative_analysis = {
            'analysis_mode': 'specific_multiple',
            'source_job': individual_analyses[0]['source_job'],  # Same for all
            'target_count': len(individual_analyses),
            'transitions': individual_analyses,
            'comparative_metrics': {
                'highest_similarity': individual_analyses[0]['transition_metrics']['similarity_score'],
                'lowest_similarity': individual_analyses[-1]['transition_metrics']['similarity_score'],
                'average_similarity': round(sum(t['transition_metrics']['similarity_score'] for t in individual_analyses) / len(individual_analyses), 1),
                'similarity_range_spread': round(individual_analyses[0]['transition_metrics']['similarity_score'] - individual_analyses[-1]['transition_metrics']['similarity_score'], 1)
            },
            'strategic_portfolio': self._generate_portfolio_analysis(individual_analyses),
            'recommendations_rank': self._rank_transition_recommendations(individual_analyses)
        }
        
        logger.info(f"Multiple transition analysis complete: {len(individual_analyses)} valid transitions analyzed")
        return comparative_analysis
    
    def get_available_targets(self, job_from: str, similarity_range: Tuple[float, float] = (0.4, 0.9), 
                            limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get available target jobs within similarity range for suggestions.
        
        Args:
            job_from: Source JobProfileID
            similarity_range: (min_similarity, max_similarity) tuple
            limit: Maximum number of results to return
            
        Returns:
            List of available target jobs with similarity scores
        """
        logger.info(f"Getting available targets for {job_from} in range {similarity_range}")
        
        query = """
        SELECT 
            js.job_to,
            js.similarity_score * 100 as similarity_pct,
            j.JobProfile,
            j.JobFunction,
            j.ManagementLevel,
            js.shared_skills_count,
            js.total_skills_to
        FROM job_similarities js
        JOIN jobs j ON js.job_to = j.JobProfileID
        WHERE js.job_from = ? 
        AND js.similarity_score BETWEEN ? AND ?
        AND js.job_from != js.job_to  -- Exclude self-matches
        ORDER BY js.similarity_score DESC
        LIMIT ?
        """
        
        cursor = self.db.execute(query, (job_from, similarity_range[0], similarity_range[1], limit))
        results = cursor.fetchall()
        
        targets = []
        for row in results:
            targets.append({
                'job_id': row['job_to'],
                'logical_display_name': self.job_display_manager.get_display_name(row['job_to'], DisplayFormat.LOGICAL),
                'job_profile': row['JobProfile'],
                'job_function': row['JobFunction'],
                'management_level': row['ManagementLevel'],
                'similarity_score': round(row['similarity_pct'], 1),
                'shared_skills_count': row['shared_skills_count'],
                'total_skills': row['total_skills_to']
            })
        
        logger.info(f"Found {len(targets)} available targets")
        return targets
    
    def _get_transition_similarity(self, job_from: str, job_to: str) -> Optional[Dict[str, Any]]:
        """Get similarity data between two specific jobs."""
        query = """
        SELECT 
            similarity_score,
            skill_overlap_score,
            shared_skills_count,
            total_skills_from,
            total_skills_to
        FROM job_similarities 
        WHERE job_from = ? AND job_to = ?
        """
        
        cursor = self.db.execute(query, (job_from, job_to))
        result = cursor.fetchone()
        
        if result:
            return {
                'similarity_score': result['similarity_score'],
                'skill_overlap_score': result['skill_overlap_score'],
                'shared_skills_count': result['shared_skills_count'],
                'total_skills_from': result['total_skills_from'],
                'total_skills_to': result['total_skills_to']
            }
        return None
    
    def _analyze_skills_gap(self, job_from: str, job_to: str) -> Dict[str, Any]:
        """Analyze skills gap between source and target jobs."""
        query = """
        SELECT 
            s.Skill_Name,
            s.Category,
            CASE WHEN source_skills.Skill_ID IS NOT NULL THEN 1 ELSE 0 END as in_source,
            CASE WHEN target_skills.Skill_ID IS NOT NULL THEN 1 ELSE 0 END as in_target
        FROM skills s
        LEFT JOIN job_skills source_skills ON s.Skill_ID = source_skills.Skill_ID AND source_skills.JobProfileID = ?
        LEFT JOIN job_skills target_skills ON s.Skill_ID = target_skills.Skill_ID AND target_skills.JobProfileID = ?
        WHERE source_skills.Skill_ID IS NOT NULL OR target_skills.Skill_ID IS NOT NULL
        """
        
        cursor = self.db.execute(query, (job_from, job_to))
        skills_data = cursor.fetchall()
        
        shared_skills = []
        development_skills = []
        transferable_skills = []
        
        for skill in skills_data:
            skill_info = {
                'name': skill['Skill_Name'],
                'category': skill['Category']
            }
            
            if skill['in_source'] and skill['in_target']:
                shared_skills.append(skill_info)
            elif not skill['in_source'] and skill['in_target']:
                development_skills.append(skill_info)
            elif skill['in_source'] and not skill['in_target']:
                transferable_skills.append(skill_info)
        
        return {
            'shared_skills': shared_skills,
            'development_skills': development_skills,
            'transferable_skills': transferable_skills,
            'shared_skills_count': len(shared_skills),
            'development_skills_count': len(development_skills),
            'transferable_skills_count': len(transferable_skills),
            'skills_gap_percentage': round((len(development_skills) / (len(shared_skills) + len(development_skills))) * 100, 1) if (len(shared_skills) + len(development_skills)) > 0 else 0
        }
    
    def _classify_career_move(self, job_from: str, job_to: str, similarity_score: float) -> Dict[str, Any]:
        """Classify the type of career move and assess difficulty."""
        source_context = self._get_job_context(job_from)
        target_context = self._get_job_context(job_to)
        
        # Determine move type
        same_function = source_context['job_function'] == target_context['job_function']
        level_change = self._compare_management_levels(
            source_context['management_level'], 
            target_context['management_level']
        )
        
        if same_function and level_change == 'same':
            move_type = 'lateral_within_function'
        elif same_function and level_change == 'promotion':
            move_type = 'vertical_promotion'
        elif same_function and level_change == 'demotion':
            move_type = 'vertical_step_back'
        elif not same_function and level_change == 'same':
            move_type = 'cross_functional_lateral'
        elif not same_function and level_change == 'promotion':
            move_type = 'cross_functional_promotion'
        else:
            move_type = 'cross_functional_expansion'
        
        # Assess difficulty
        if similarity_score >= 0.8:
            difficulty = 'low'
            timeline = '3-6 months'
        elif similarity_score >= 0.6:
            difficulty = 'moderate'
            timeline = '6-9 months'
        elif similarity_score >= 0.4:
            difficulty = 'high'
            timeline = '9-12 months'
        else:
            difficulty = 'very_high'
            timeline = '12+ months'
        
        return {
            'move_type': move_type,
            'move_type_display': move_type.replace('_', ' ').title(),
            'difficulty_level': difficulty,
            'difficulty_display': difficulty.replace('_', ' ').title(),
            'estimated_timeline': timeline,
            'level_transition': level_change,
            'cross_functional': not same_function,
            'same_function': same_function
        }
    
    def _get_job_context(self, job_id: str) -> Dict[str, Any]:
        """Get contextual information about a job."""
        # Note: Division is in positions table, not jobs table
        query = """
        SELECT j.JobProfile, j.JobFunction, j.ManagementLevel, j.JobCategory
        FROM jobs j
        WHERE j.JobProfileID = ?
        """
        
        cursor = self.db.execute(query, (job_id,))
        result = cursor.fetchone()
        
        if result:
            return {
                'job_profile': result['JobProfile'],
                'job_function': result['JobFunction'],
                'management_level': result['ManagementLevel'],
                'job_category': result['JobCategory']  # Use JobCategory instead of Division
            }
        return {}
    
    def _compare_management_levels(self, level_from: str, level_to: str) -> str:
        """Compare management levels to determine promotion/lateral/demotion."""
        # Based on the schema, ManagementLevel values are: Group 1, Group 2, Group 3, etc.
        level_hierarchy = {
            'Group 1': 1,
            'Group 2': 2, 
            'Group 3': 3,
            'Group 4': 4,
            'Group 5': 5,
            'Group 6': 6,
            'Group 7': 7,
            'Group NA': 0  # Special case for non-applicable
        }
        
        from_rank = level_hierarchy.get(level_from, 0)
        to_rank = level_hierarchy.get(level_to, 0)
        
        if to_rank > from_rank:
            return 'promotion'
        elif to_rank < from_rank:
            return 'demotion'
        else:
            return 'same'
    
    def _calculate_similarity_percentile(self, similarity_score: float) -> int:
        """Calculate what percentile this similarity score represents."""
        query = """
        SELECT COUNT(*) as total_count,
               SUM(CASE WHEN similarity_score <= ? THEN 1 ELSE 0 END) as below_or_equal
        FROM job_similarities
        WHERE job_from != job_to
        """
        
        cursor = self.db.execute(query, (similarity_score,))
        result = cursor.fetchone()
        
        if result and result['total_count'] > 0:
            percentile = round((result['below_or_equal'] / result['total_count']) * 100)
            return min(99, max(1, percentile))  # Clamp between 1-99
        return 50  # Default if no data
    
    def _check_similarity_range(self, similarity_score: float, similarity_range: Tuple[float, float]) -> bool:
        """Check if similarity score falls within specified range."""
        return similarity_range[0] <= similarity_score <= similarity_range[1]
    
    def _generate_strategic_context(self, source_context: Dict, target_context: Dict, 
                                  transition_data: Dict, move_classification: Dict) -> Dict[str, Any]:
        """Generate strategic context for the transition."""
        return {
            'transition_viability': 'high' if transition_data['similarity_score'] >= 0.6 else 'moderate' if transition_data['similarity_score'] >= 0.4 else 'challenging',
            'strategic_rationale': self._generate_strategic_rationale(source_context, target_context, move_classification),
            'business_impact': self._assess_business_impact(move_classification),
            'development_focus': 'skills_enhancement' if move_classification['same_function'] else 'cross_functional_adaptation'
        }
    
    def _generate_strategic_rationale(self, source_context: Dict, target_context: Dict, move_classification: Dict) -> str:
        """Generate strategic rationale for the transition."""
        if move_classification['cross_functional']:
            return f"Cross-functional transition from {source_context.get('job_function', 'unknown')} to {target_context.get('job_function', 'unknown')} broadens capabilities and market value."
        else:
            return f"Within-function progression in {source_context.get('job_function', 'unknown')} deepens specialization and expertise."
    
    def _assess_business_impact(self, move_classification: Dict) -> str:
        """Assess the business impact of the transition."""
        if move_classification['level_transition'] == 'promotion':
            return 'high_value_leadership_development'
        elif move_classification['cross_functional']:
            return 'strategic_capability_expansion'
        else:
            return 'expertise_deepening'
    
    def _generate_portfolio_analysis(self, individual_analyses: List[Dict]) -> Dict[str, Any]:
        """Generate portfolio analysis for multiple transitions."""
        function_diversity = len(set(a['target_job']['job_function'] for a in individual_analyses))
        level_diversity = len(set(a['target_job']['management_level'] for a in individual_analyses))
        
        return {
            'portfolio_strength': 'high' if function_diversity >= 3 else 'moderate' if function_diversity >= 2 else 'focused',
            'function_diversity_count': function_diversity,
            'level_diversity_count': level_diversity,
            'strategic_coverage': 'comprehensive' if function_diversity >= 3 and level_diversity >= 2 else 'targeted'
        }
    
    def _rank_transition_recommendations(self, individual_analyses: List[Dict]) -> List[Dict[str, Any]]:
        """Rank transitions with strategic recommendations."""
        rankings = []
        for i, analysis in enumerate(individual_analyses, 1):
            rankings.append({
                'rank': i,
                'job_id': analysis['target_job']['job_id'],
                'logical_display_name': analysis['target_job']['logical_display_name'],
                'similarity_score': analysis['transition_metrics']['similarity_score'],
                'strategic_priority': 'primary' if i == 1 else 'secondary' if i <= 3 else 'alternative',
                'recommendation_rationale': self._generate_recommendation_rationale(analysis, i)
            })
        return rankings
    
    def _generate_recommendation_rationale(self, analysis: Dict, rank: int) -> str:
        """Generate recommendation rationale for a ranked transition."""
        similarity = analysis['transition_metrics']['similarity_score']
        move_type = analysis['move_classification']['move_type_display']
        
        if rank == 1:
            return f"Highest similarity ({similarity}%) with {move_type.lower()} progression - recommended primary target."
        elif rank <= 3:
            return f"Strong similarity ({similarity}%) offering {move_type.lower()} opportunity - strategic secondary option."
        else:
            return f"Viable transition ({similarity}%) for {move_type.lower()} - consider as alternative pathway." 