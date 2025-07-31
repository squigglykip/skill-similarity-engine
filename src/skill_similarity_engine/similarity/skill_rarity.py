"""
Skill Rarity Analysis Module

Handles skill universe loading, prevalence calculation, and rarity categorization.
This module provides the foundation for identifying rare/defining skills that are
crucial for the rarity-weighted similarity algorithm.

Based on empirically-tuned rarity thresholds:
- Rare: <5% prevalence (defining skills)
- Uncommon: 5-20% prevalence  
- Common: 20-50% prevalence
- Universal: >50% prevalence
"""

import logging
import sqlite3
import pandas as pd
from typing import Dict, Any, Optional
from ..utils.progress import progress_context

# Rarity thresholds for skill categorisation (empirically-tuned)
RARITY_THRESHOLDS = {
    'rare': 5.0,        # <5% = rare (defining skills)
    'uncommon': 20.0,   # 5-20% = uncommon
    'common': 50.0,     # 20-50% = common
    # >50% = universal
}


class SkillRarityAnalyzer:
    """
    Analyzes skill rarity and prevalence across job profiles.
    
    This class handles loading the skill universe from the database,
    calculating prevalence percentages, and categorizing skills by rarity.
    """
    
    def __init__(self, 
                 rarity_thresholds: Optional[Dict[str, float]] = None):
        """
        Initialize the skill rarity analyzer.
        
        Args:
            rarity_thresholds: Custom rarity thresholds (default: empirically-tuned values)
        """
        self.rarity_thresholds = rarity_thresholds or RARITY_THRESHOLDS
        self.logger = logging.getLogger(__name__)
        
    def load_skill_universe_from_database(self, db_path: str) -> pd.DataFrame:
        """
        Load active skill universe with prevalence calculations from database.
        
        Only includes skills that are actually used in job profiles.
        
        Args:
            db_path: Path to the SQLite database
            
        Returns:
            DataFrame with active skills, prevalence percentages, and rarity categories
        """
        self.logger.info("Loading active skill universe from database...")
        
        try:
            conn = sqlite3.connect(db_path)
            
            # Get total job profiles for prevalence calculation
            total_profiles_query = "SELECT COUNT(DISTINCT JobProfileID) as total FROM core_job_architecture"
            total_profiles_result = pd.read_sql_query(total_profiles_query, conn)
            total_profiles = total_profiles_result.iloc[0]['total']
            
            # Calculate skill prevalence across job profiles - ONLY for skills that are actually used
            skill_prevalence_query = f"""
            SELECT 
                s.Skill_ID,
                s.Skill_Name,
                s.Category,
                s.Subcategory,
                s.SkillType,
                COUNT(DISTINCT js.JobProfileID) as job_profiles_with_skill,
                COUNT(DISTINCT js.JobProfileID) * 100.0 / {total_profiles} as prevalence_percentage
            FROM core_skills_taxonomy s
            INNER JOIN core_job_skill_requirements js ON s.Skill_ID = js.Skill_ID
            GROUP BY s.Skill_ID, s.Skill_Name, s.Category, s.Subcategory, s.SkillType
            ORDER BY prevalence_percentage ASC
            """
            
            skill_universe = pd.read_sql_query(skill_prevalence_query, conn)
            conn.close()
            
            # Categorise by rarity
            skill_universe['rarity_category'] = skill_universe['prevalence_percentage'].apply(
                self.categorise_rarity
            )
            
            self.logger.info(f"Loaded {len(skill_universe):,} active skills (skills used in job profiles)")
            self.logger.info(f"Total job profiles: {total_profiles:,}")
            
            # Show rarity distribution
            rarity_dist = skill_universe['rarity_category'].value_counts()
            self.logger.info("Rarity distribution:")
            for category, count in rarity_dist.items():
                percentage = (count / len(skill_universe)) * 100
                self.logger.info(f"  • {category}: {count:,} skills ({percentage:.1f}%)")
            
            return skill_universe
            
        except sqlite3.Error as e:
            self.logger.error(f"Database error while loading skill universe: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error loading skill universe: {e}")
            raise
    
    def categorise_rarity(self, prevalence_percentage: float) -> str:
        """
        Categorise skill by rarity based on prevalence percentage.
        
        Args:
            prevalence_percentage: Percentage of job profiles that use this skill
            
        Returns:
            Rarity category string ('Rare', 'Uncommon', 'Common', 'Universal')
        """
        if prevalence_percentage < self.rarity_thresholds['rare']:
            return 'Rare'
        elif prevalence_percentage < self.rarity_thresholds['uncommon']:
            return 'Uncommon'
        elif prevalence_percentage < self.rarity_thresholds['common']:
            return 'Common'
        else:
            return 'Universal'
    
    def generate_skill_rarity_analysis(self, skill_universe: pd.DataFrame) -> pd.DataFrame:
        """
        Generate comprehensive skill rarity analysis for database population.
        
        Args:
            skill_universe: DataFrame with skill prevalence data
            
        Returns:
            DataFrame formatted for analytics_skill_rarity table
        """
        self.logger.info("Generating skill rarity analysis...")
        
        # Create rarity analysis records
        rarity_records = []
        
        with progress_context(
            total=len(skill_universe),
            desc="Skill Rarity Analysis",
            memory_tracking=True,
            show_tqdm=True
        ) as progress:
            
            for _, skill_row in skill_universe.iterrows():
                rarity_record = {
                    'skill_id': skill_row['Skill_ID'],
                    'skill_name': skill_row['Skill_Name'],
                    'category': skill_row['Category'],
                    'subcategory': skill_row.get('Subcategory', ''),
                    'skill_type': skill_row['SkillType'],
                    'total_profiles_with_skill': int(skill_row['job_profiles_with_skill']),
                    'total_jobs': 715,  # Total job profiles in database
                    'prevalence_percentage': round(skill_row['prevalence_percentage'], 2),
                    'rarity_category': skill_row['rarity_category'],
                    'rarity_score': self._calculate_rarity_score(skill_row['prevalence_percentage']),
                    'is_defining_skill': skill_row['rarity_category'] == 'Rare',
                    'defining_for_jobs_count': 0,  # Will be populated later
                    'defining_for_jobs': '',  # Will be populated later
                    'analysis_date': pd.Timestamp.now().strftime('%Y-%m-%d'),
                    'algorithm_version': 'rarity_analyzer_v1.0'
                }
                
                rarity_records.append(rarity_record)
                progress.update(1)
        
        rarity_df = pd.DataFrame(rarity_records)
        
        self.logger.info(f"Generated rarity analysis for {len(rarity_df):,} skills")
        
        # Show summary statistics
        rare_count = len(rarity_df[rarity_df['is_defining_skill']])
        self.logger.info(f"Rare skills (defining): {rare_count:,} ({rare_count/len(rarity_df)*100:.1f}%)")
        
        return rarity_df
    
    def get_rare_skills(self, skill_universe: pd.DataFrame, threshold: float = None) -> pd.DataFrame:
        """
        Get skills classified as rare (defining skills).
        
        Args:
            skill_universe: DataFrame with skill prevalence data
            threshold: Custom rarity threshold (default: uses configured rare threshold)
            
        Returns:
            DataFrame containing only rare skills
        """
        if threshold is None:
            threshold = self.rarity_thresholds['rare']
            
        rare_skills = skill_universe[
            skill_universe['prevalence_percentage'] < threshold
        ].copy()
        
        self.logger.info(f"Found {len(rare_skills):,} rare skills (prevalence < {threshold}%)")
        
        return rare_skills
    
    def get_rarity_summary(self, skill_universe: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate summary statistics for skill rarity distribution.
        
        Args:
            skill_universe: DataFrame with skill prevalence data
            
        Returns:
            Dict with rarity distribution statistics
        """
        total_skills = len(skill_universe)
        rarity_dist = skill_universe['rarity_category'].value_counts()
        
        summary = {
            'total_skills': total_skills,
            'rarity_distribution': rarity_dist.to_dict(),
            'rarity_percentages': {
                category: round((count / total_skills) * 100, 1)
                for category, count in rarity_dist.items()
            },
            'rare_skills_count': rarity_dist.get('Rare', 0),
            'rare_skills_percentage': round((rarity_dist.get('Rare', 0) / total_skills) * 100, 1),
            'avg_prevalence': round(skill_universe['prevalence_percentage'].mean(), 2),
            'median_prevalence': round(skill_universe['prevalence_percentage'].median(), 2),
            'min_prevalence': round(skill_universe['prevalence_percentage'].min(), 2),
            'max_prevalence': round(skill_universe['prevalence_percentage'].max(), 2)
        }
        
        return summary
    
    def _calculate_rarity_score(self, prevalence_percentage: float) -> float:
        """
        Calculate a normalized rarity score (0-100, where 100 = most rare).
        
        Args:
            prevalence_percentage: Skill prevalence percentage
            
        Returns:
            Rarity score (0-100)
        """
        # Invert prevalence so rare skills get high scores
        # Cap at 100% to handle edge cases
        capped_prevalence = min(prevalence_percentage, 100.0)
        rarity_score = 100.0 - capped_prevalence
        
        return round(rarity_score, 2)