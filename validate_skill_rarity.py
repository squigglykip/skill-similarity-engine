#!/usr/bin/env python3
"""
Skill Rarity Analysis Validation

This script validates that our skill rarity calculations are correct by:
1. Manually calculating skill prevalence from core data
2. Comparing with analytics_skill_rarity table results
3. Validating rarity categorization logic
4. Ensuring the foundation for defining skills is solid

Key Validations:
- Prevalence percentage calculation: (jobs_with_skill / total_jobs) * 100
- Rarity categorization: Rare (≤5%), Uncommon (5-20%), Common (20-50%), Universal (>50%)
- Total skill count and job count consistency
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Rarity thresholds (matching our configuration)
RARITY_THRESHOLDS = {
    'rare': 5.0,        # ≤ 5%
    'uncommon': 20.0,   # 5-20%  
    'common': 50.0,     # 20-50%
    # universal: > 50%
}


class SkillRarityValidator:
    """Validates skill rarity calculations and categorization"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        
        # Load data for validation
        self.total_jobs = self._get_total_job_count()
        self.manual_skill_prevalence = self._calculate_manual_skill_prevalence()
        self.database_skill_rarity = self._load_database_skill_rarity()
        
        logger.info(f"Loaded {self.total_jobs} total jobs for rarity calculation")
        logger.info(f"Calculated prevalence for {len(self.manual_skill_prevalence)} skills manually")
        logger.info(f"Loaded {len(self.database_skill_rarity)} skills from analytics table")
    
    def _get_total_job_count(self) -> int:
        """Get total number of job profiles"""
        query = "SELECT COUNT(DISTINCT JobProfileID) FROM core_job_architecture"
        cursor = self.conn.execute(query)
        return cursor.fetchone()[0]
    
    def _calculate_manual_skill_prevalence(self) -> Dict[str, Dict[str, Any]]:
        """Manually calculate skill prevalence from core data"""
        logger.info("Manually calculating skill prevalence from core data...")
        
        # Get all job-skill relationships with skill details
        query = """
        SELECT 
            st.Skill_ID,
            st.Skill_Name,
            st.Category,
            st.Subcategory,
            st.SkillType,
            jsr.JobProfileID
        FROM core_skills_taxonomy st
        JOIN core_job_skill_requirements jsr ON st.Skill_ID = jsr.Skill_ID
        """
        
        df = pd.read_sql_query(query, self.conn)
        
        # Count jobs per skill
        skill_job_counts = defaultdict(set)
        skill_details = {}
        
        for _, row in df.iterrows():
            skill_id = row['Skill_ID']
            skill_job_counts[skill_id].add(row['JobProfileID'])
            
            # Store skill details (same for all instances)
            if skill_id not in skill_details:
                skill_details[skill_id] = {
                    'skill_name': row['Skill_Name'],
                    'category': row['Category'],
                    'subcategory': row['Subcategory'],
                    'skill_type': row['SkillType']
                }
        
        # Calculate prevalence and categorize
        skill_prevalence = {}
        for skill_id, job_set in skill_job_counts.items():
            job_count = len(job_set)
            prevalence_percentage = (job_count / self.total_jobs) * 100
            
            # Categorize by rarity
            if prevalence_percentage <= RARITY_THRESHOLDS['rare']:
                rarity_category = 'Rare'
            elif prevalence_percentage <= RARITY_THRESHOLDS['uncommon']:
                rarity_category = 'Uncommon'
            elif prevalence_percentage <= RARITY_THRESHOLDS['common']:
                rarity_category = 'Common'
            else:
                rarity_category = 'Universal'
            
            skill_prevalence[skill_id] = {
                **skill_details[skill_id],
                'job_count': job_count,
                'prevalence_percentage': round(prevalence_percentage, 2),
                'rarity_category': rarity_category
            }
        
        return skill_prevalence
    
    def _load_database_skill_rarity(self) -> Dict[str, Dict[str, Any]]:
        """Load skill rarity data from analytics table"""
        query = """
        SELECT 
            skill_id,
            skill_name,
            category,
            subcategory,
            skill_type,
            total_profiles_with_skill,
            prevalence_percentage,
            rarity_category
        FROM analytics_skill_rarity
        """
        
        df = pd.read_sql_query(query, self.conn)
        return df.set_index('skill_id').to_dict('index')
    
    def validate_skill_rarity_calculations(self) -> Dict[str, Any]:
        """Validate skill rarity calculations against database"""
        logger.info("Validating skill rarity calculations...")
        
        validation_results = {
            'total_skills_manual': len(self.manual_skill_prevalence),
            'total_skills_database': len(self.database_skill_rarity),
            'exact_matches': 0,
            'close_matches': 0,  # Within 0.01% difference
            'category_mismatches': 0,
            'missing_from_database': 0,
            'extra_in_database': 0,
            'detailed_results': []
        }
        
        # Check each manually calculated skill
        for skill_id, manual_data in self.manual_skill_prevalence.items():
            if skill_id not in self.database_skill_rarity:
                validation_results['missing_from_database'] += 1
                validation_results['detailed_results'].append({
                    'skill_id': skill_id,
                    'skill_name': manual_data['skill_name'],
                    'status': 'MISSING_FROM_DB',
                    'manual_prevalence': manual_data['prevalence_percentage'],
                    'manual_category': manual_data['rarity_category']
                })
                continue
            
            db_data = self.database_skill_rarity[skill_id]
            
            # Compare prevalence percentages
            prevalence_diff = abs(manual_data['prevalence_percentage'] - db_data['prevalence_percentage'])
            category_match = manual_data['rarity_category'] == db_data['rarity_category']
            
            if prevalence_diff < 0.001 and category_match:
                validation_results['exact_matches'] += 1
                match_status = 'EXACT_MATCH'
            elif prevalence_diff < 0.01 and category_match:
                validation_results['close_matches'] += 1
                match_status = 'CLOSE_MATCH'
            elif not category_match:
                validation_results['category_mismatches'] += 1
                match_status = 'CATEGORY_MISMATCH'
            else:
                match_status = 'PREVALENCE_DIFFERENCE'
            
            validation_results['detailed_results'].append({
                'skill_id': skill_id,
                'skill_name': manual_data['skill_name'],
                'status': match_status,
                'manual_prevalence': manual_data['prevalence_percentage'],
                'db_prevalence': db_data['prevalence_percentage'],
                'prevalence_diff': prevalence_diff,
                'manual_category': manual_data['rarity_category'],
                'db_category': db_data['rarity_category'],
                'manual_job_count': manual_data['job_count'],
                'db_job_count': db_data['total_profiles_with_skill']
            })
        
        # Check for extra skills in database
        for skill_id in self.database_skill_rarity:
            if skill_id not in self.manual_skill_prevalence:
                validation_results['extra_in_database'] += 1
        
        return validation_results
    
    def analyze_rarity_distribution(self) -> Dict[str, Any]:
        """Analyze the distribution of skills across rarity categories"""
        logger.info("Analyzing rarity distribution...")
        
        # Manual distribution
        manual_categories = defaultdict(int)
        for skill_data in self.manual_skill_prevalence.values():
            manual_categories[skill_data['rarity_category']] += 1
        
        # Database distribution
        db_categories = defaultdict(int)
        for skill_data in self.database_skill_rarity.values():
            db_categories[skill_data['rarity_category']] += 1
        
        return {
            'manual_distribution': dict(manual_categories),
            'database_distribution': dict(db_categories),
            'total_manual': len(self.manual_skill_prevalence),
            'total_database': len(self.database_skill_rarity)
        }
    
    def get_sample_skills_by_category(self, category: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get sample skills from a specific rarity category"""
        samples = []
        count = 0
        
        for skill_id, skill_data in self.manual_skill_prevalence.items():
            if skill_data['rarity_category'] == category and count < limit:
                db_data = self.database_skill_rarity.get(skill_id, {})
                samples.append({
                    'skill_name': skill_data['skill_name'],
                    'category': skill_data['category'],
                    'manual_prevalence': skill_data['prevalence_percentage'],
                    'db_prevalence': db_data.get('prevalence_percentage', 'N/A'),
                    'job_count': skill_data['job_count']
                })
                count += 1
        
        return samples


def main():
    """Main validation function"""
    print("🔍 Skill Rarity Analysis Validation")
    print("=" * 60)
    print()
    print("Validating foundation component: Skill prevalence and rarity categorization")
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
    validator = SkillRarityValidator(str(db_path))
    
    # Validate skill rarity calculations
    print("🧮 Validating Skill Rarity Calculations...")
    print("-" * 40)
    
    validation_results = validator.validate_skill_rarity_calculations()
    
    # Print validation results
    total_manual = validation_results['total_skills_manual']
    total_db = validation_results['total_skills_database']
    exact_matches = validation_results['exact_matches']
    close_matches = validation_results['close_matches']
    category_mismatches = validation_results['category_mismatches']
    missing = validation_results['missing_from_database']
    extra = validation_results['extra_in_database']
    
    print(f"📊 Validation Results:")
    print(f"   • Manual calculation: {total_manual:,} skills")
    print(f"   • Database records: {total_db:,} skills")
    print(f"   • ✅ Exact matches: {exact_matches:,}")
    print(f"   • 🟡 Close matches (≤0.01% diff): {close_matches:,}")
    print(f"   • ⚠️ Category mismatches: {category_mismatches:,}")
    print(f"   • ❌ Missing from database: {missing:,}")
    print(f"   • ➕ Extra in database: {extra:,}")
    
    if total_manual > 0:
        accuracy = (exact_matches + close_matches) / total_manual * 100
        print(f"   • 🎯 Overall accuracy: {accuracy:.1f}%")
    
    print()
    
    # Analyze rarity distribution
    print("📈 Rarity Distribution Analysis:")
    print("-" * 40)
    
    distribution = validator.analyze_rarity_distribution()
    
    print("Manual Calculation vs Database:")
    categories = ['Rare', 'Uncommon', 'Common', 'Universal']
    for category in categories:
        manual_count = distribution['manual_distribution'].get(category, 0)
        db_count = distribution['database_distribution'].get(category, 0)
        manual_pct = (manual_count / distribution['total_manual']) * 100 if distribution['total_manual'] > 0 else 0
        db_pct = (db_count / distribution['total_database']) * 100 if distribution['total_database'] > 0 else 0
        
        status = "✅" if manual_count == db_count else "⚠️"
        print(f"   {status} {category}: Manual {manual_count:,} ({manual_pct:.1f}%) | DB {db_count:,} ({db_pct:.1f}%)")
    
    print()
    
    # Show sample skills from each category
    print("📋 Sample Skills by Rarity Category:")
    print("-" * 40)
    
    for category in categories:
        samples = validator.get_sample_skills_by_category(category, limit=3)
        if samples:
            print(f"\n{category} Skills:")
            for sample in samples:
                prevalence_match = "✅" if abs(sample['manual_prevalence'] - (sample['db_prevalence'] if isinstance(sample['db_prevalence'], (int, float)) else 0)) < 0.01 else "⚠️"
                print(f"   {prevalence_match} {sample['skill_name']} ({sample['category']})")
                print(f"      Prevalence: {sample['manual_prevalence']:.2f}% | Jobs: {sample['job_count']}")
    
    print()
    
    # Show any significant mismatches
    mismatches = [r for r in validation_results['detailed_results'] 
                 if r['status'] in ['CATEGORY_MISMATCH', 'PREVALENCE_DIFFERENCE']]
    
    if mismatches:
        print("⚠️ Significant Differences Found:")
        print("-" * 40)
        for mismatch in mismatches[:10]:  # Show first 10
            print(f"   {mismatch['skill_name']} ({mismatch['skill_id']})")
            print(f"      Manual: {mismatch['manual_prevalence']:.2f}% ({mismatch['manual_category']})")
            print(f"      Database: {mismatch['db_prevalence']:.2f}% ({mismatch['db_category']})")
            print(f"      Difference: {mismatch['prevalence_diff']:.4f}%")
            print()
    
    # Overall assessment
    print("=" * 60)
    if accuracy >= 99:
        print("🎉 EXCELLENT: Skill rarity calculations are highly accurate!")
        print("   The foundation for defining skills analysis is solid.")
    elif accuracy >= 95:
        print("✅ GOOD: Skill rarity calculations are mostly accurate.")
        print("   Minor discrepancies may be due to data processing differences.")
    else:
        print("⚠️ ATTENTION NEEDED: Significant differences in skill rarity calculations.")
        print("   Review the skill rarity analysis algorithm and data processing.")
    
    print(f"\n🎯 Skill Rarity Validation: {'PASSED' if accuracy >= 95 else 'NEEDS REVIEW'}")
    print("   This component provides the foundation for defining skills identification.")
    print("=" * 60)


if __name__ == "__main__":
    main()