#!/usr/bin/env python3
"""
Phase 1 Enhanced Similarity Validation Script

This script manually calculates enhanced similarity scores for a sample of job pairs
and compares them with the stored results in the analytics database to validate
the correctness of our enhanced similarity algorithm.

Key Algorithm Components:
1. Asymmetric Jaccard Similarity: |A ∩ B| / |A|
2. Defining Skills: Top 20% rarest skills per job
3. Rarity Boost: 1.05x multiplier when both jobs share defining skills
4. Skill Rarity Categories: Rare (≤5%), Uncommon (5-15%), Common (15-50%), Universal (>50%)
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

# Algorithm constants (matching our modular components)
DEFINING_SKILLS_PERCENTILE = 0.20  # Top 20% rarest skills
GENTLE_MULTIPLIER = 1.05           # 5% bonus for shared defining skills
RARITY_THRESHOLDS = {
    'rare': 0.05,      # ≤ 5%
    'uncommon': 0.15,  # 5-15%
    'common': 0.50,    # 15-50%
    # universal: > 50%
}


class ManualSimilarityCalculator:
    """Manual implementation of enhanced similarity algorithm for validation"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        
        # Load core data
        self.skills_data = self._load_skills_data()
        self.job_skills_data = self._load_job_skills_data()
        self.skill_rarity = self._calculate_skill_rarity()
        self.job_defining_skills = self._calculate_job_defining_skills()
        
        logger.info(f"Loaded {len(self.skills_data)} skills and {len(self.job_skills_data)} jobs")
        logger.info(f"Calculated rarity for {len(self.skill_rarity)} skills")
        logger.info(f"Calculated defining skills for {len(self.job_defining_skills)} jobs")
    
    def _load_skills_data(self) -> Dict[str, Dict]:
        """Load skills taxonomy data"""
        query = """
        SELECT Skill_ID, Skill_Name, SkillType, Category, Subcategory
        FROM core_skills_taxonomy
        """
        df = pd.read_sql_query(query, self.conn)
        return df.set_index('Skill_ID').to_dict('index')
    
    def _load_job_skills_data(self) -> Dict[str, Set[str]]:
        """Load job-skill relationships"""
        query = """
        SELECT DISTINCT ja.JobProfileID, js.Skill_ID
        FROM core_job_architecture ja
        JOIN core_job_skill_requirements js ON ja.JobProfileID = js.JobProfileID
        """
        df = pd.read_sql_query(query, self.conn)
        
        job_skills = defaultdict(set)
        for _, row in df.iterrows():
            job_skills[row['JobProfileID']].add(row['Skill_ID'])
        
        return dict(job_skills)
    
    def _calculate_skill_rarity(self) -> Dict[str, str]:
        """Calculate skill rarity categories based on prevalence"""
        total_jobs = len(self.job_skills_data)
        skill_counts = defaultdict(int)
        
        # Count how many jobs use each skill
        for job_id, skills in self.job_skills_data.items():
            for skill_id in skills:
                skill_counts[skill_id] += 1
        
        # Categorize by rarity
        skill_rarity = {}
        for skill_id, count in skill_counts.items():
            prevalence = count / total_jobs
            
            if prevalence <= RARITY_THRESHOLDS['rare']:
                skill_rarity[skill_id] = 'rare'
            elif prevalence <= RARITY_THRESHOLDS['uncommon']:
                skill_rarity[skill_id] = 'uncommon'
            elif prevalence <= RARITY_THRESHOLDS['common']:
                skill_rarity[skill_id] = 'common'
            else:
                skill_rarity[skill_id] = 'universal'
        
        return skill_rarity
    
    def _calculate_job_defining_skills(self) -> Dict[str, Set[str]]:
        """Calculate top 20% rarest skills per job (defining skills)"""
        job_defining_skills = {}
        
        for job_id, skills in self.job_skills_data.items():
            # Get rarity scores for job's skills (lower = rarer)
            skill_rarity_scores = []
            for skill_id in skills:
                rarity_category = self.skill_rarity.get(skill_id, 'universal')
                if rarity_category == 'rare':
                    score = 1
                elif rarity_category == 'uncommon':
                    score = 2
                elif rarity_category == 'common':
                    score = 3
                else:  # universal
                    score = 4
                skill_rarity_scores.append((skill_id, score))
            
            # Sort by rarity (ascending - most rare first)
            skill_rarity_scores.sort(key=lambda x: x[1])
            
            # Take top 20% as defining skills
            num_defining = max(1, int(len(skill_rarity_scores) * DEFINING_SKILLS_PERCENTILE))
            defining_skills = {skill_id for skill_id, _ in skill_rarity_scores[:num_defining]}
            
            job_defining_skills[job_id] = defining_skills
        
        return job_defining_skills
    
    def calculate_enhanced_similarity(self, job_a_id: str, job_b_id: str) -> Dict[str, Any]:
        """
        Manually calculate enhanced similarity between two jobs
        
        Returns detailed breakdown of the calculation
        """
        skills_a = self.job_skills_data.get(job_a_id, set())
        skills_b = self.job_skills_data.get(job_b_id, set())
        defining_a = self.job_defining_skills.get(job_a_id, set())
        defining_b = self.job_defining_skills.get(job_b_id, set())
        
        if not skills_a or not skills_b:
            return {
                'job_from': job_a_id,
                'job_to': job_b_id,
                'similarity_score': 0.0,
                'base_similarity': 0.0,
                'defining_skills_boost': 0.0,
                'shared_skills': 0,
                'total_skills_a': 0,
                'shared_defining_skills': 0,
                'error': 'One or both jobs have no skills'
            }
        
        # Base asymmetric Jaccard similarity: |A ∩ B| / |A|
        shared_skills = skills_a.intersection(skills_b)
        base_similarity = len(shared_skills) / len(skills_a)
        
        # Check for shared defining skills boost
        shared_defining = defining_a.intersection(defining_b)
        has_shared_defining = len(shared_defining) > 0
        
        # Apply gentle multiplier if both jobs share defining skills
        if has_shared_defining:
            enhanced_similarity = base_similarity * GENTLE_MULTIPLIER
            boost_applied = (GENTLE_MULTIPLIER - 1.0) * base_similarity
        else:
            enhanced_similarity = base_similarity
            boost_applied = 0.0
        
        return {
            'job_from': job_a_id,
            'job_to': job_b_id,
            'similarity_score': round(enhanced_similarity, 6),
            'base_similarity': round(base_similarity, 6),
            'defining_skills_boost': round(boost_applied, 6),
            'shared_skills': len(shared_skills),
            'total_skills_a': len(skills_a),
            'shared_defining_skills': len(shared_defining),
            'has_shared_defining': has_shared_defining
        }
    
    def get_database_similarity(self, job_a_id: str, job_b_id: str) -> Dict[str, Any]:
        """Get similarity score from analytics database"""
        query = """
        SELECT similarity_score, shared_skills_count, total_skills_from,
               defining_skill_boost, shared_defining_skills_count
        FROM analytics_job_similarities
        WHERE job_from = ? AND job_to = ?
        """
        
        cursor = self.conn.execute(query, (job_a_id, job_b_id))
        result = cursor.fetchone()
        
        if result:
            return {
                'job_from': job_a_id,
                'job_to': job_b_id,
                'similarity_score': result[0],
                'shared_skills': result[1],
                'total_skills_from': result[2],
                'defining_skill_boost': result[3],
                'shared_defining_skills': result[4]
            }
        else:
            return None
    
    def validate_sample_calculations(self, sample_size: int = 10) -> Dict[str, Any]:
        """Validate a sample of similarity calculations"""
        # Get a sample of job pairs from the database
        query = """
        SELECT DISTINCT job_from, job_to
        FROM analytics_job_similarities
        ORDER BY RANDOM()
        LIMIT ?
        """
        
        sample_pairs = pd.read_sql_query(query, self.conn, params=(sample_size,))
        
        validation_results = {
            'total_tested': 0,
            'matches': 0,
            'mismatches': 0,
            'errors': 0,
            'details': []
        }
        
        logger.info(f"Validating {len(sample_pairs)} random job pairs...")
        
        for _, row in sample_pairs.iterrows():
            job_a_id = row['job_from']
            job_b_id = row['job_to']
            
            try:
                # Manual calculation
                manual_result = self.calculate_enhanced_similarity(job_a_id, job_b_id)
                
                # Database result
                db_result = self.get_database_similarity(job_a_id, job_b_id)
                
                if db_result is None:
                    validation_results['errors'] += 1
                    validation_results['details'].append({
                        'job_pair': f"{job_a_id} -> {job_b_id}",
                        'status': 'ERROR',
                        'issue': 'No database record found'
                    })
                    continue
                
                # Compare results (with small tolerance for floating point)
                similarity_match = abs(manual_result['similarity_score'] - db_result['similarity_score']) < 0.000001
                shared_skills_match = manual_result['shared_skills'] == db_result['shared_skills']
                total_skills_match = manual_result['total_skills_a'] == db_result['total_skills_from']
                
                if similarity_match and shared_skills_match and total_skills_match:
                    validation_results['matches'] += 1
                    status = 'MATCH'
                else:
                    validation_results['mismatches'] += 1
                    status = 'MISMATCH'
                
                validation_results['details'].append({
                    'job_pair': f"{job_a_id} -> {job_b_id}",
                    'status': status,
                    'manual_similarity': manual_result['similarity_score'],
                    'db_similarity': db_result['similarity_score'],
                    'manual_shared': manual_result['shared_skills'],
                    'db_shared': db_result['shared_skills'],
                    'manual_total': manual_result['total_skills_a'],
                    'db_total': db_result['total_skills_from'],
                    'has_defining_boost': manual_result['has_shared_defining']
                })
                
                validation_results['total_tested'] += 1
                
            except Exception as e:
                validation_results['errors'] += 1
                validation_results['details'].append({
                    'job_pair': f"{job_a_id} -> {job_b_id}",
                    'status': 'ERROR',
                    'issue': str(e)
                })
        
        return validation_results


def main():
    """Main validation function"""
    print("🔍 Phase 1 Enhanced Similarity Validation")
    print("=" * 60)
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
    
    # Initialize manual calculator
    calculator = ManualSimilarityCalculator(str(db_path))
    
    # Validate sample calculations
    print("🧮 Validating Enhanced Similarity Calculations...")
    print("-" * 40)
    
    validation_results = calculator.validate_sample_calculations(sample_size=20)
    
    # Print results
    print(f"📊 Validation Results:")
    print(f"   • Total tested: {validation_results['total_tested']}")
    print(f"   • ✅ Matches: {validation_results['matches']}")
    print(f"   • ❌ Mismatches: {validation_results['mismatches']}")
    print(f"   • ⚠️ Errors: {validation_results['errors']}")
    
    if validation_results['total_tested'] > 0:
        accuracy = validation_results['matches'] / validation_results['total_tested'] * 100
        print(f"   • 🎯 Accuracy: {accuracy:.1f}%")
    
    print()
    
    # Show detailed results for first few
    print("📋 Sample Validation Details:")
    print("-" * 40)
    
    for i, detail in enumerate(validation_results['details'][:10]):
        status_icon = "✅" if detail['status'] == 'MATCH' else "❌" if detail['status'] == 'MISMATCH' else "⚠️"
        print(f"{status_icon} {detail['job_pair']}: {detail['status']}")
        
        if detail['status'] in ['MATCH', 'MISMATCH']:
            print(f"    Manual: {detail['manual_similarity']:.6f} | DB: {detail['db_similarity']:.6f}")
            print(f"    Shared: {detail['manual_shared']} | Total: {detail['manual_total']} | Boost: {detail['has_defining_boost']}")
        elif detail['status'] == 'ERROR':
            print(f"    Issue: {detail['issue']}")
        print()
    
    # Overall assessment
    if validation_results['matches'] == validation_results['total_tested']:
        print("🎉 All calculations match! Enhanced similarity algorithm is working correctly.")
    elif validation_results['matches'] > validation_results['total_tested'] * 0.95:
        print("✅ Most calculations match. Minor discrepancies may be due to floating point precision.")
    else:
        print("⚠️ Significant mismatches found. Algorithm may need review.")
    
    print("\n" + "=" * 60)
    print("🔍 Validation complete!")


if __name__ == "__main__":
    main()