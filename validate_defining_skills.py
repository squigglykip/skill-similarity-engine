#!/usr/bin/env python3
"""
Defining Skills per Job Profile Validation

This script validates that our defining skills selection is correct by:
1. Manually calculating the top 8.8% rarest skills for each job
2. Comparing with analytics_job_defining_skills table results
3. Validating the defining skills logic matches our business requirements
4. Ensuring the critical component for enhanced similarity is working

Key Validations:
- Top 8.8% rarest skills selection per job (Optuna-optimized threshold)
- Correct skill ranking by rarity (prevalence percentage ascending)
- Proper handling of edge cases (jobs with few skills)
- Consistency with skill rarity analysis
"""

import sys
import os
import sqlite3
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Set, List, Tuple, Any
from collections import defaultdict

# Add src to path for imports
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

from skill_similarity_engine.models.versioning import ModelVersionManager
from skill_similarity_engine.config.architectural_config_manager import get_config_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class DefiningSkillsValidator:
    """Validates defining skills selection for each job profile"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        
        # Load current configuration (Optuna-optimized)
        self.config_manager = get_config_manager()
        self.similarity_params = self.config_manager.get_nested_value(
            'core', 'similarity_parameters', 'optuna_optimal',
            default={'defining_skills_percentile': 8.8}
        )
        
        self.DEFINING_SKILLS_PERCENTILE = self.similarity_params.get('defining_skills_percentile', 8.8) / 100.0
        
        logger.info(f"Using defining skills threshold: {self.DEFINING_SKILLS_PERCENTILE * 100:.1f}%")
        
        # Load data for validation
        self.job_profiles = self._load_job_profiles()
        self.skill_rarity_data = self._load_skill_rarity_data()
        self.job_skill_relationships = self._load_job_skill_relationships()
        self.manual_defining_skills = self._calculate_manual_defining_skills()
        self.database_defining_skills = self._load_database_defining_skills()
        
        logger.info(f"Loaded {len(self.job_profiles)} job profiles")
        logger.info(f"Loaded rarity data for {len(self.skill_rarity_data)} skills")
        logger.info(f"Calculated defining skills for {len(self.manual_defining_skills)} jobs manually")
        logger.info(f"Loaded defining skills for {len(self.database_defining_skills)} jobs from database")
    
    def _load_job_profiles(self) -> Dict[str, Dict[str, str]]:
        """Load job profiles with details"""
        query = """
        SELECT JobProfileID, JobProfile, JobFunction, ManagementLevel, JobCategory
        FROM core_job_architecture
        """
        df = pd.read_sql_query(query, self.conn)
        return df.set_index('JobProfileID').to_dict('index')
    
    def _load_skill_rarity_data(self) -> Dict[str, Dict[str, Any]]:
        """Load skill rarity data for prevalence ranking"""
        query = """
        SELECT skill_id, skill_name, prevalence_percentage, rarity_category
        FROM analytics_skill_rarity
        """
        df = pd.read_sql_query(query, self.conn)
        return df.set_index('skill_id').to_dict('index')
    
    def _load_job_skill_relationships(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load job-skill relationships with skill details"""
        query = """
        SELECT 
            ja.JobProfileID,
            st.Skill_ID,
            st.Skill_Name,
            st.Category,
            st.SkillType
        FROM core_job_architecture ja
        JOIN core_job_skill_requirements jsr ON ja.JobProfileID = jsr.JobProfileID
        JOIN core_skills_taxonomy st ON jsr.Skill_ID = st.Skill_ID
        ORDER BY ja.JobProfileID, st.Skill_Name
        """
        
        df = pd.read_sql_query(query, self.conn)
        
        job_skills = defaultdict(list)
        for _, row in df.iterrows():
            job_skills[row['JobProfileID']].append({
                'skill_id': row['Skill_ID'],
                'skill_name': row['Skill_Name'],
                'category': row['Category'],
                'skill_type': row['SkillType']
            })
        
        return dict(job_skills)
    
    def _calculate_manual_defining_skills(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Manually calculate defining skills using exact business logic.
        Replicates the logic from defining_skills.py
        """
        logger.info(f"Manually calculating defining skills using {self.DEFINING_SKILLS_PERCENTILE * 100:.1f}% threshold...")
        
        job_defining_skills = {}
        
        for job_id, job_skills in self.job_skill_relationships.items():
            # Get skills with their rarity data
            skills_with_rarity = []
            
            for skill_info in job_skills:
                skill_id = skill_info['skill_id']
                rarity_data = self.skill_rarity_data.get(skill_id)
                
                if rarity_data:
                    skills_with_rarity.append({
                        'skill_id': skill_id,
                        'skill_name': skill_info['skill_name'],
                        'category': skill_info['category'],
                        'skill_type': skill_info['skill_type'],
                        'prevalence_percentage': rarity_data['prevalence_percentage'],
                        'rarity_category': rarity_data['rarity_category']
                    })
            
            # Sort by prevalence (ascending = rarest first), then by skill name for deterministic tie-breaking
            skills_with_rarity.sort(key=lambda x: (x['prevalence_percentage'], x['skill_name']))
            
            # Take top X% rarest skills (using exact logic from defining_skills.py line 98)
            num_defining = max(1, int(len(skills_with_rarity) * self.DEFINING_SKILLS_PERCENTILE))
            defining_skills = skills_with_rarity[:num_defining]
            
            # Add ranking information
            for rank, skill in enumerate(defining_skills, 1):
                skill['defining_skill_rank'] = rank
                skill['defining_skill_score'] = 100.0 - skill['prevalence_percentage']
            
            job_defining_skills[job_id] = defining_skills
        
        return job_defining_skills
    
    def _load_database_defining_skills(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load defining skills from analytics database"""
        query = """
        SELECT 
            job_profile_id,
            skill_id,
            skill_name,
            category,
            skill_type,
            prevalence_percentage,
            rarity_category,
            defining_skill_rank,
            defining_skill_score
        FROM analytics_job_defining_skills
        ORDER BY job_profile_id, defining_skill_rank
        """
        
        df = pd.read_sql_query(query, self.conn)
        
        job_defining_skills = defaultdict(list)
        for _, row in df.iterrows():
            job_defining_skills[row['job_profile_id']].append({
                'skill_id': row['skill_id'],
                'skill_name': row['skill_name'],
                'category': row['category'],
                'skill_type': row['skill_type'],
                'prevalence_percentage': row['prevalence_percentage'],
                'rarity_category': row['rarity_category'],
                'defining_skill_rank': row['defining_skill_rank'],
                'defining_skill_score': row['defining_skill_score']
            })
        
        return dict(job_defining_skills)
    
    def validate_defining_skills_selection(self) -> Dict[str, Any]:
        """Validate defining skills selection against database"""
        logger.info("Validating defining skills selection...")
        
        validation_results = {
            'total_jobs_manual': len(self.manual_defining_skills),
            'total_jobs_database': len(self.database_defining_skills),
            'exact_matches': 0,
            'count_matches': 0,  # Same number of defining skills
            'skill_set_matches': 0,  # Same skills selected
            'ranking_matches': 0,  # Same skill ranking
            'count_mismatches': 0,
            'skill_selection_differences': 0,
            'missing_jobs': 0,
            'detailed_results': []
        }
        
        # Check each job
        for job_id, manual_skills in self.manual_defining_skills.items():
            if job_id not in self.database_defining_skills:
                validation_results['missing_jobs'] += 1
                continue
            
            db_skills = self.database_defining_skills[job_id]
            
            # Compare counts
            manual_count = len(manual_skills)
            db_count = len(db_skills)
            count_match = manual_count == db_count
            
            if count_match:
                validation_results['count_matches'] += 1
            else:
                validation_results['count_mismatches'] += 1
            
            # Compare skill sets (same skills selected)
            manual_skill_ids = {skill['skill_id'] for skill in manual_skills}
            db_skill_ids = {skill['skill_id'] for skill in db_skills}
            skill_set_match = manual_skill_ids == db_skill_ids
            
            if skill_set_match:
                validation_results['skill_set_matches'] += 1
            else:
                validation_results['skill_selection_differences'] += 1
            
            # Compare rankings (if same skills selected)
            ranking_match = False
            if skill_set_match and count_match:
                ranking_match = True
                for manual_skill in manual_skills:
                    manual_rank = manual_skill['defining_skill_rank']
                    # Find corresponding DB skill
                    db_skill = next((s for s in db_skills if s['skill_id'] == manual_skill['skill_id']), None)
                    if db_skill and db_skill['defining_skill_rank'] != manual_rank:
                        ranking_match = False
                        break
                
                if ranking_match:
                    validation_results['ranking_matches'] += 1
            
            # Overall match assessment
            if count_match and skill_set_match and ranking_match:
                validation_results['exact_matches'] += 1
                match_status = 'EXACT_MATCH'
            elif count_match and skill_set_match:
                match_status = 'RANKING_DIFFERENCE'
            elif count_match:
                match_status = 'SKILL_SELECTION_DIFFERENCE'
            else:
                match_status = 'COUNT_DIFFERENCE'
            
            # Store detailed result
            job_name = self.job_profiles.get(job_id, {}).get('JobProfile', 'Unknown')
            
            detailed_result = {
                'job_id': job_id,
                'job_name': job_name,
                'status': match_status,
                'manual_count': manual_count,
                'db_count': db_count,
                'count_match': count_match,
                'skill_set_match': skill_set_match,
                'ranking_match': ranking_match,
                'manual_skills': [s['skill_name'] for s in manual_skills],
                'db_skills': [s['skill_name'] for s in db_skills],
                'skills_only_in_manual': list(manual_skill_ids - db_skill_ids),
                'skills_only_in_db': list(db_skill_ids - manual_skill_ids)
            }
            
            validation_results['detailed_results'].append(detailed_result)
        
        return validation_results
    
    def analyze_defining_skills_distribution(self) -> Dict[str, Any]:
        """Analyze distribution of defining skills counts per job"""
        logger.info("Analyzing defining skills distribution...")
        
        # Manual distribution
        manual_counts = [len(skills) for skills in self.manual_defining_skills.values()]
        
        # Database distribution
        db_counts = [len(skills) for skills in self.database_defining_skills.values()]
        
        return {
            'manual_stats': {
                'min': min(manual_counts) if manual_counts else 0,
                'max': max(manual_counts) if manual_counts else 0,
                'avg': sum(manual_counts) / len(manual_counts) if manual_counts else 0,
                'total_defining_skills': sum(manual_counts)
            },
            'database_stats': {
                'min': min(db_counts) if db_counts else 0,
                'max': max(db_counts) if db_counts else 0,
                'avg': sum(db_counts) / len(db_counts) if db_counts else 0,
                'total_defining_skills': sum(db_counts)
            }
        }
    
    def get_sample_job_defining_skills(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get sample jobs with their defining skills for inspection"""
        samples = []
        count = 0
        
        for job_id, manual_skills in self.manual_defining_skills.items():
            if count >= limit:
                break
            
            job_name = self.job_profiles.get(job_id, {}).get('JobProfile', 'Unknown')
            db_skills = self.database_defining_skills.get(job_id, [])
            
            samples.append({
                'job_id': job_id,
                'job_name': job_name,
                'total_skills': len(self.job_skill_relationships.get(job_id, [])),
                'manual_defining_count': len(manual_skills),
                'db_defining_count': len(db_skills),
                'manual_defining_skills': [
                    {
                        'name': skill['skill_name'],
                        'prevalence': skill['prevalence_percentage'],
                        'rank': skill['defining_skill_rank']
                    }
                    for skill in manual_skills
                ],
                'db_defining_skills': [
                    {
                        'name': skill['skill_name'],
                        'prevalence': skill['prevalence_percentage'],
                        'rank': skill['defining_skill_rank']
                    }
                    for skill in db_skills
                ]
            })
            count += 1
        
        return samples


def main():
    """Main validation function"""
    print("🎯 Defining Skills per Job Profile Validation")
    print("=" * 60)
    print()
    print("Validating critical component: Top 8.8% rarest skills selection per job")
    print("This component directly impacts enhanced similarity calculations.")
    print()
    
    # Setup database path
    version_manager = ModelVersionManager()
    output_dir = version_manager.setup_output_directory(interactive=False, output_type='business_context')
    db_path = output_dir / 'business_context.sqlite'
    
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return
    
    print(f"📊 Database: {db_path}")
    print()
    
    # Initialize validator
    validator = DefiningSkillsValidator(str(db_path))
    
    # Validate defining skills selection
    print("🧮 Validating Defining Skills Selection...")
    print("-" * 40)
    
    validation_results = validator.validate_defining_skills_selection()
    
    # Print validation results
    total_manual = validation_results['total_jobs_manual']
    total_db = validation_results['total_jobs_database']
    exact_matches = validation_results['exact_matches']
    count_matches = validation_results['count_matches']
    skill_set_matches = validation_results['skill_set_matches']
    ranking_matches = validation_results['ranking_matches']
    missing_jobs = validation_results['missing_jobs']
    
    print(f"📊 Validation Results:")
    print(f"   • Manual calculation: {total_manual:,} jobs")
    print(f"   • Database records: {total_db:,} jobs")
    print(f"   • ✅ Exact matches: {exact_matches:,}")
    print(f"   • 🔢 Count matches: {count_matches:,}")
    print(f"   • 🎯 Skill set matches: {skill_set_matches:,}")
    print(f"   • 📈 Ranking matches: {ranking_matches:,}")
    print(f"   • ❌ Missing jobs: {missing_jobs:,}")
    
    if total_manual > 0:
        accuracy = exact_matches / total_manual * 100
        skill_accuracy = skill_set_matches / total_manual * 100
        print(f"   • 🎯 Exact match accuracy: {accuracy:.1f}%")
        print(f"   • 🎯 Skill selection accuracy: {skill_accuracy:.1f}%")
    
    print()
    
    # Analyze distribution
    print("📈 Defining Skills Distribution Analysis:")
    print("-" * 40)
    
    distribution = validator.analyze_defining_skills_distribution()
    
    manual_stats = distribution['manual_stats']
    db_stats = distribution['database_stats']
    
    print("Manual Calculation vs Database:")
    print(f"   Min defining skills per job: {manual_stats['min']} | {db_stats['min']}")
    print(f"   Max defining skills per job: {manual_stats['max']} | {db_stats['max']}")
    print(f"   Avg defining skills per job: {manual_stats['avg']:.1f} | {db_stats['avg']:.1f}")
    print(f"   Total defining skills: {manual_stats['total_defining_skills']:,} | {db_stats['total_defining_skills']:,}")
    
    print()
    
    # Show sample job defining skills
    print("📋 Sample Job Defining Skills Analysis:")
    print("-" * 40)
    
    samples = validator.get_sample_job_defining_skills(limit=5)
    
    for sample in samples:
        match_status = "✅" if sample['manual_defining_count'] == sample['db_defining_count'] else "⚠️"
        print(f"\n{match_status} {sample['job_name']} ({sample['job_id']})")
        print(f"   Total skills: {sample['total_skills']} | Defining: Manual {sample['manual_defining_count']} | DB {sample['db_defining_count']}")
        
        # Show defining skills comparison
        if sample['manual_defining_skills']:
            print("   Manual defining skills:")
            for skill in sample['manual_defining_skills'][:3]:  # Show top 3
                print(f"     {skill['rank']}. {skill['name']} ({skill['prevalence']:.2f}%)")
        
        if sample['db_defining_skills']:
            print("   Database defining skills:")
            for skill in sample['db_defining_skills'][:3]:  # Show top 3
                print(f"     {skill['rank']}. {skill['name']} ({skill['prevalence']:.2f}%)")
    
    print()
    
    # Show any significant differences
    differences = [r for r in validation_results['detailed_results'] 
                  if r['status'] != 'EXACT_MATCH']
    
    if differences:
        print("⚠️ Jobs with Differences:")
        print("-" * 40)
        for diff in differences[:5]:  # Show first 5
            print(f"   {diff['job_name']} ({diff['job_id']}): {diff['status']}")
            print(f"      Counts: Manual {diff['manual_count']} | DB {diff['db_count']}")
            
            if diff['skills_only_in_manual']:
                print(f"      Only in manual: {diff['skills_only_in_manual'][:3]}")
            if diff['skills_only_in_db']:
                print(f"      Only in DB: {diff['skills_only_in_db'][:3]}")
            print()
    
    # Overall assessment
    print("=" * 60)
    if accuracy >= 99:
        print("🎉 EXCELLENT: Defining skills selection is highly accurate!")
        print("   The 8.8% threshold is being applied correctly across all jobs.")
    elif accuracy >= 95:
        print("✅ GOOD: Defining skills selection is mostly accurate.")
        print("   Minor discrepancies may be due to edge cases or rounding differences.")
    else:
        print("⚠️ ATTENTION NEEDED: Significant differences in defining skills selection.")
        print("   Review the defining skills algorithm and threshold application.")
    
    print(f"\n🎯 Defining Skills Validation: {'PASSED' if accuracy >= 95 else 'NEEDS REVIEW'}")
    print("   This component is critical for enhanced similarity boost calculations.")
    print("=" * 60)


if __name__ == "__main__":
    main()