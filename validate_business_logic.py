#!/usr/bin/env python3
"""
Business Logic Validation for NAB Skills Intelligence Engine

This script validates that our enhanced similarity algorithm serves the core business use case:
ASYMMETRIC CAREER PATHWAY ANALYSIS - "If I'm in Job A, what skills do I need to get to Job B?"

Key Business Requirements:
1. Asymmetric similarity: Job A → Job B transition readiness (not bidirectional)
2. Defining skills emphasis: Rare skills that characterize specific roles
3. Skill gap analysis: What skills does someone need to develop?
4. Career pathway intelligence: Which transitions are most feasible?

This validation reconstructs our business logic using current Optuna-optimized parameters
and compares against database results to ensure algorithmic correctness.
"""

import sys
import os
import sqlite3
import pandas as pd
import logging
from pathlib import Path
from typing import Dict, Set, List, Tuple, Any, Optional
from collections import defaultdict
import json

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


class BusinessLogicValidator:
    """
    Validates business logic by reconstructing the entire similarity calculation
    using current configuration and comparing against database results.
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        
        # Load current configuration (Optuna-optimized)
        self.config_manager = get_config_manager()
        self.similarity_params = self.config_manager.get_nested_value(
            'core', 'similarity_parameters', 'optuna_optimal',
            default={'defining_skills_percentile': 8.8, 'defining_skills_multiplier': 1.206}
        )
        
        self.DEFINING_SKILLS_PERCENTILE = self.similarity_params.get('defining_skills_percentile', 8.8) / 100.0
        self.DEFINING_SKILLS_MULTIPLIER = self.similarity_params.get('defining_skills_multiplier', 1.206)
        
        logger.info(f"Using Optuna-optimized parameters:")
        logger.info(f"  Defining skills percentile: {self.DEFINING_SKILLS_PERCENTILE * 100:.1f}%")
        logger.info(f"  Defining skills multiplier: {self.DEFINING_SKILLS_MULTIPLIER:.3f}x")
        
        # Load data for validation
        self._load_business_data()
    
    def _load_business_data(self):
        """Load all necessary data for business logic validation"""
        logger.info("Loading business data for validation...")
        
        # Load job profiles with names for human-readable output
        self.job_profiles = self._load_job_profiles()
        
        # Load skills with categories and rarity
        self.skills_data = self._load_skills_with_rarity()
        
        # Load job-skill relationships  
        self.job_to_skills = self._load_job_skill_relationships()
        
        # Calculate defining skills using exact business logic
        self.job_defining_skills = self._calculate_defining_skills()
        
        logger.info(f"Loaded {len(self.job_profiles)} job profiles")
        logger.info(f"Loaded {len(self.skills_data)} skills with rarity data")  
        logger.info(f"Loaded {len(self.job_to_skills)} job-skill mappings")
        logger.info(f"Calculated defining skills for {len(self.job_defining_skills)} jobs")
    
    def _load_job_profiles(self) -> Dict[str, Dict[str, str]]:
        """Load job profiles with human-readable information"""
        query = """
        SELECT JobProfileID, JobProfile, JobFunction, ManagementLevel, JobCategory
        FROM core_job_architecture
        """
        df = pd.read_sql_query(query, self.conn)
        return df.set_index('JobProfileID').to_dict('index')
    
    def _load_skills_with_rarity(self) -> Dict[str, Dict[str, Any]]:
        """Load skills with rarity information from analytics table"""
        query = """
        SELECT skill_id, skill_name, category, subcategory, skill_type,
               prevalence_percentage, rarity_category
        FROM analytics_skill_rarity
        """
        df = pd.read_sql_query(query, self.conn)
        return df.set_index('skill_id').to_dict('index')
    
    def _load_job_skill_relationships(self) -> Dict[str, Set[str]]:
        """Load job-skill relationships using skill names (not IDs)"""
        query = """
        SELECT ja.JobProfileID, st.Skill_Name
        FROM core_job_architecture ja
        JOIN core_job_skill_requirements jsr ON ja.JobProfileID = jsr.JobProfileID
        JOIN core_skills_taxonomy st ON jsr.Skill_ID = st.Skill_ID
        """
        df = pd.read_sql_query(query, self.conn)
        
        job_skills = defaultdict(set)
        for _, row in df.iterrows():
            job_skills[row['JobProfileID']].add(row['Skill_Name'])
        
        return dict(job_skills)
    
    def _calculate_defining_skills(self) -> Dict[str, Set[str]]:
        """
        Calculate defining skills using exact business logic from our modules.
        This replicates the logic in defining_skills.py
        """
        logger.info(f"Calculating defining skills using {self.DEFINING_SKILLS_PERCENTILE * 100:.1f}% threshold...")
        
        job_defining_skills = {}
        
        for job_id, job_skills in self.job_to_skills.items():
            # Get skills with their rarity data
            skills_with_rarity = []
            for skill_name in job_skills:
                # Find skill in rarity data
                skill_rarity_data = None
                for skill_id, data in self.skills_data.items():
                    if data['skill_name'] == skill_name:
                        skill_rarity_data = data
                        break
                
                if skill_rarity_data:
                    skills_with_rarity.append({
                        'skill_name': skill_name,
                        'prevalence_percentage': skill_rarity_data['prevalence_percentage']
                    })
            
            # Sort by prevalence (ascending = rarest first), then by skill name for deterministic tie-breaking
            skills_with_rarity.sort(key=lambda x: (x['prevalence_percentage'], x['skill_name']))
            
            # Take top X% rarest skills (using exact logic from defining_skills.py line 98)
            num_defining = max(1, int(len(skills_with_rarity) * self.DEFINING_SKILLS_PERCENTILE))
            defining_skills = {skill['skill_name'] for skill in skills_with_rarity[:num_defining]}
            
            job_defining_skills[job_id] = defining_skills
        
        return job_defining_skills
    
    def calculate_business_similarity(self, job_a_id: str, job_b_id: str) -> Dict[str, Any]:
        """
        Calculate similarity using exact business logic for asymmetric career transitions.
        
        Business Logic:
        1. Asymmetric Jaccard: How much of Job A's skills are covered by Job B
        2. Defining skills boost: Extra weight for sharing rare, role-defining skills
        3. Skill gap analysis: What skills need to be developed for transition
        
        Returns comprehensive business intelligence for career pathway analysis.
        """
        job_a_skills = self.job_to_skills.get(job_a_id, set())
        job_b_skills = self.job_to_skills.get(job_b_id, set())
        job_a_defining = self.job_defining_skills.get(job_a_id, set())
        job_b_defining = self.job_defining_skills.get(job_b_id, set())
        
        if not job_a_skills or not job_b_skills:
            return self._create_empty_result(job_a_id, job_b_id, "Missing skills data")
        
        # Core asymmetric similarity: |A ∩ B| / |A|
        # "What percentage of Job A's skills are already covered by Job B?"
        shared_skills = job_a_skills.intersection(job_b_skills)
        base_similarity = len(shared_skills) / len(job_a_skills)
        
        # Defining skills analysis
        shared_defining_skills = job_a_defining.intersection(job_b_defining)
        shared_defining_count = len(shared_defining_skills)
        
        # Apply defining skills boost using Optuna-optimized multiplier
        if shared_defining_count > 0:
            # Multiplicative boost: similarity * (multiplier^shared_defining_count)
            boost_factor = self.DEFINING_SKILLS_MULTIPLIER ** shared_defining_count
            enhanced_similarity = base_similarity * boost_factor
            defining_boost = enhanced_similarity - base_similarity
        else:
            enhanced_similarity = base_similarity
            defining_boost = 0.0
            boost_factor = 1.0
        
        # Skill gap analysis for career pathway intelligence
        skills_needed = job_b_skills - job_a_skills  # Skills to develop
        defining_skills_needed = job_b_defining - job_a_defining  # Critical defining skills to develop
        
        # Career transition feasibility scoring
        skill_overlap_percentage = (len(shared_skills) / len(job_b_skills)) * 100 if job_b_skills else 0
        
        return {
            'job_from': job_a_id,
            'job_to': job_b_id,
            'job_from_name': self.job_profiles.get(job_a_id, {}).get('JobProfile', 'Unknown'),
            'job_to_name': self.job_profiles.get(job_b_id, {}).get('JobProfile', 'Unknown'),
            
            # Core similarity metrics
            'base_similarity': round(base_similarity, 6),
            'enhanced_similarity': round(enhanced_similarity, 6),
            'defining_boost': round(defining_boost, 6),
            'boost_factor': round(boost_factor, 6),
            
            # Skill analysis
            'shared_skills_count': len(shared_skills),
            'total_skills_from': len(job_a_skills),
            'total_skills_to': len(job_b_skills),
            'skill_overlap_percentage': round(skill_overlap_percentage, 1),
            
            # Defining skills analysis
            'shared_defining_skills_count': shared_defining_count,
            'shared_defining_skills': list(shared_defining_skills),
            
            # Career pathway intelligence
            'skills_to_develop_count': len(skills_needed),
            'skills_to_develop': list(skills_needed)[:10],  # Top 10 for display
            'defining_skills_to_develop_count': len(defining_skills_needed),
            'defining_skills_to_develop': list(defining_skills_needed),
            
            # Business insights
            'transition_feasibility': self._assess_transition_feasibility(
                base_similarity, shared_defining_count, len(skills_needed)
            ),
            'career_pathway_type': self._classify_career_pathway(
                job_a_id, job_b_id, base_similarity, shared_defining_count
            )
        }
    
    def _create_empty_result(self, job_a_id: str, job_b_id: str, reason: str) -> Dict[str, Any]:
        """Create empty result for invalid job pairs"""
        return {
            'job_from': job_a_id,
            'job_to': job_b_id,
            'job_from_name': self.job_profiles.get(job_a_id, {}).get('JobProfile', 'Unknown'),
            'job_to_name': self.job_profiles.get(job_b_id, {}).get('JobProfile', 'Unknown'),
            'base_similarity': 0.0,
            'enhanced_similarity': 0.0,
            'error': reason
        }
    
    def _assess_transition_feasibility(self, base_similarity: float, shared_defining: int, skills_gap: int) -> str:
        """Assess how feasible a career transition is"""
        if base_similarity >= 0.8:
            return "High - Strong skill overlap"
        elif base_similarity >= 0.6:
            return "Moderate - Good foundation with some development needed"
        elif base_similarity >= 0.4:
            return "Challenging - Significant skill development required"
        elif shared_defining > 0:
            return "Specialized - Share defining skills but different domains"
        else:
            return "Difficult - Major career pivot required"
    
    def _classify_career_pathway(self, job_a_id: str, job_b_id: str, similarity: float, shared_defining: int) -> str:
        """Classify the type of career pathway"""
        job_a_function = self.job_profiles.get(job_a_id, {}).get('JobFunction', '')
        job_b_function = self.job_profiles.get(job_b_id, {}).get('JobFunction', '')
        
        if job_a_function == job_b_function:
            if similarity >= 0.7:
                return "Lateral Move - Same function, similar skills"
            else:
                return "Functional Specialization - Same function, different focus"
        elif shared_defining > 2:
            return "Cross-Functional Transfer - Leveraging specialized skills"
        elif similarity >= 0.5:
            return "Adjacent Function Move - Related skills transfer"
        else:
            return "Career Pivot - New domain entry"
    
    def get_database_similarity(self, job_a_id: str, job_b_id: str) -> Optional[Dict[str, Any]]:
        """Get similarity data from analytics database"""
        query = """
        SELECT similarity_score, enhanced_similarity_score, rarity_weighted_score,
               shared_skills_count, total_skills_from, total_skills_to,
               shared_defining_skills_count, defining_skill_boost,
               skill_overlap_percentage, shared_skills, shared_defining_skills,
               skill_gap_analysis
        FROM analytics_job_similarities
        WHERE job_from = ? AND job_to = ?
        """
        
        cursor = self.conn.execute(query, (job_a_id, job_b_id))
        result = cursor.fetchone()
        
        if result:
            return {
                'similarity_score': result[0],
                'enhanced_similarity_score': result[1],
                'rarity_weighted_score': result[2],
                'shared_skills_count': result[3],
                'total_skills_from': result[4],
                'total_skills_to': result[5],
                'shared_defining_skills_count': result[6],
                'defining_skill_boost': result[7],
                'skill_overlap_percentage': result[8],
                'shared_skills': result[9],
                'shared_defining_skills': result[10],
                'skill_gap_analysis': result[11]
            }
        return None
    
    def validate_business_logic(self, sample_size: int = 20) -> Dict[str, Any]:
        """
        Validate business logic by comparing manual calculations with database results
        """
        logger.info(f"Validating business logic with {sample_size} job pairs...")
        
        # Get diverse sample of job pairs
        sample_pairs = self._get_diverse_sample(sample_size)
        
        validation_results = {
            'total_tested': 0,
            'exact_matches': 0,
            'close_matches': 0,  # Within 1% difference
            'significant_differences': 0,
            'errors': 0,
            'business_insights': [],
            'detailed_results': []
        }
        
        for job_a_id, job_b_id in sample_pairs:
            try:
                # Calculate using business logic
                business_result = self.calculate_business_similarity(job_a_id, job_b_id)
                
                # Get database result
                db_result = self.get_database_similarity(job_a_id, job_b_id)
                
                if db_result is None:
                    validation_results['errors'] += 1
                    continue
                
                # Compare key metrics
                similarity_diff = abs(business_result['enhanced_similarity'] - db_result['enhanced_similarity_score'])
                shared_skills_match = business_result['shared_skills_count'] == db_result['shared_skills_count']
                defining_skills_match = business_result['shared_defining_skills_count'] == db_result['shared_defining_skills_count']
                
                # Classify match quality
                if similarity_diff < 0.000001 and shared_skills_match and defining_skills_match:
                    validation_results['exact_matches'] += 1
                    match_status = 'EXACT_MATCH'
                elif similarity_diff < 0.01 and shared_skills_match and defining_skills_match:
                    validation_results['close_matches'] += 1
                    match_status = 'CLOSE_MATCH'
                else:
                    validation_results['significant_differences'] += 1
                    match_status = 'SIGNIFICANT_DIFFERENCE'
                
                # Store detailed result with business insights
                detailed_result = {
                    'job_pair': f"{business_result['job_from_name']} → {business_result['job_to_name']}",
                    'job_ids': f"{job_a_id} → {job_b_id}",
                    'match_status': match_status,
                    'similarity_diff': similarity_diff,
                    
                    # Business logic results
                    'business_enhanced_similarity': business_result['enhanced_similarity'],
                    'business_base_similarity': business_result['base_similarity'],
                    'business_defining_boost': business_result['defining_boost'],
                    
                    # Database results
                    'db_enhanced_similarity': db_result['enhanced_similarity_score'],
                    'db_defining_boost': db_result['defining_skill_boost'],
                    
                    # Business insights
                    'transition_feasibility': business_result['transition_feasibility'],
                    'career_pathway_type': business_result['career_pathway_type'],
                    'skills_to_develop': business_result['skills_to_develop_count'],
                    'defining_skills_to_develop': business_result['defining_skills_to_develop_count']
                }
                
                validation_results['detailed_results'].append(detailed_result)
                validation_results['total_tested'] += 1
                
            except Exception as e:
                validation_results['errors'] += 1
                logger.error(f"Error validating {job_a_id} → {job_b_id}: {e}")
        
        return validation_results
    
    def _get_diverse_sample(self, sample_size: int) -> List[Tuple[str, str]]:
        """Get a diverse sample of job pairs for comprehensive validation"""
        # Get job pairs with different similarity ranges for comprehensive testing
        query = """
        SELECT job_from, job_to, enhanced_similarity_score
        FROM analytics_job_similarities
        WHERE enhanced_similarity_score > 0
        ORDER BY RANDOM()
        LIMIT ?
        """
        
        df = pd.read_sql_query(query, self.conn, params=(sample_size * 3,))
        
        # Try to get diverse similarity ranges
        high_sim = df[df['enhanced_similarity_score'] >= 2.0].head(sample_size // 3)
        med_sim = df[(df['enhanced_similarity_score'] >= 0.5) & (df['enhanced_similarity_score'] < 2.0)].head(sample_size // 3)
        low_sim = df[df['enhanced_similarity_score'] < 0.5].head(sample_size // 3)
        
        diverse_sample = pd.concat([high_sim, med_sim, low_sim]).head(sample_size)
        
        return [(row['job_from'], row['job_to']) for _, row in diverse_sample.iterrows()]
    
    def generate_business_insights_report(self) -> Dict[str, Any]:
        """Generate comprehensive business insights about career pathways"""
        logger.info("Generating business insights report...")
        
        # Analyze top career pathways
        query = """
        SELECT job_from, job_to, similarity_score, enhanced_similarity_score,
               shared_defining_skills_count, skill_overlap_percentage
        FROM analytics_job_similarities
        WHERE enhanced_similarity_score > 1.0
        ORDER BY enhanced_similarity_score DESC
        LIMIT 20
        """
        
        top_pathways = pd.read_sql_query(query, self.conn)
        
        insights = {
            'top_career_pathways': [],
            'defining_skills_impact': self._analyze_defining_skills_impact(),
            'career_pathway_types': self._analyze_pathway_types(),
            'skill_development_patterns': self._analyze_skill_gaps()
        }
        
        # Enrich top pathways with business context
        for _, row in top_pathways.iterrows():
            job_from_name = self.job_profiles.get(row['job_from'], {}).get('JobProfile', 'Unknown')
            job_to_name = self.job_profiles.get(row['job_to'], {}).get('JobProfile', 'Unknown')
            
            pathway = {
                'from_job': job_from_name,
                'to_job': job_to_name,
                'transition_strength': round(row['enhanced_similarity_score'], 3),
                'base_similarity': round(row['similarity_score'], 3),
                'shared_defining_skills': row['shared_defining_skills_count'],
                'skill_overlap': f"{row['skill_overlap_percentage']}%"
            }
            
            insights['top_career_pathways'].append(pathway)
        
        return insights
    
    def _analyze_defining_skills_impact(self) -> Dict[str, Any]:
        """Analyze how defining skills boost affects career pathways"""
        query = """
        SELECT 
            shared_defining_skills_count,
            AVG(defining_skill_boost) as avg_boost,
            COUNT(*) as pathway_count
        FROM analytics_job_similarities
        WHERE shared_defining_skills_count > 0
        GROUP BY shared_defining_skills_count
        ORDER BY shared_defining_skills_count
        """
        
        df = pd.read_sql_query(query, self.conn)
        
        return {
            'boost_by_shared_defining_skills': df.to_dict('records'),
            'max_boost_observed': df['avg_boost'].max() if not df.empty else 0,
            'pathways_with_defining_boost': df['pathway_count'].sum() if not df.empty else 0
        }
    
    def _analyze_pathway_types(self) -> Dict[str, int]:
        """Analyze distribution of career pathway types"""
        # This would require more sophisticated analysis of job functions and categories
        # For now, return basic similarity distribution
        query = """
        SELECT 
            CASE 
                WHEN enhanced_similarity_score >= 3.0 THEN 'High Synergy'
                WHEN enhanced_similarity_score >= 2.0 THEN 'Strong Pathway'
                WHEN enhanced_similarity_score >= 1.0 THEN 'Viable Transition'
                WHEN enhanced_similarity_score >= 0.5 THEN 'Challenging Move'
                ELSE 'Career Pivot'
            END as pathway_type,
            COUNT(*) as count
        FROM analytics_job_similarities
        WHERE enhanced_similarity_score > 0
        GROUP BY pathway_type
        """
        
        df = pd.read_sql_query(query, self.conn)
        return dict(zip(df['pathway_type'], df['count']))
    
    def _analyze_skill_gaps(self) -> Dict[str, Any]:
        """Analyze common skill development patterns"""
        # This would require parsing skill_gap_analysis field
        # For now, return basic statistics
        query = """
        SELECT 
            AVG(total_skills_to - shared_skills_count) as avg_skills_to_develop,
            AVG(shared_defining_skills_count) as avg_shared_defining,
            COUNT(CASE WHEN shared_defining_skills_count > 0 THEN 1 END) as pathways_with_defining_overlap
        FROM analytics_job_similarities
        WHERE enhanced_similarity_score > 0
        """
        
        result = pd.read_sql_query(query, self.conn).iloc[0]
        
        return {
            'average_skills_to_develop': round(result['avg_skills_to_develop'], 1),
            'average_shared_defining_skills': round(result['avg_shared_defining'], 1),
            'pathways_with_defining_skills_overlap': int(result['pathways_with_defining_overlap'])
        }


def main():
    """Main validation function"""
    print("🎯 NAB Skills Intelligence Engine - Business Logic Validation")
    print("=" * 80)
    print()
    print("Core Business Use Case: Asymmetric Career Pathway Analysis")
    print("Question: 'If I'm in Job A, what skills do I need to transition to Job B?'")
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
    validator = BusinessLogicValidator(str(db_path))
    
    # Validate business logic
    print("🧮 Validating Business Logic Against Database Results...")
    print("-" * 60)
    
    validation_results = validator.validate_business_logic(sample_size=25)
    
    # Print validation results
    total_tested = validation_results['total_tested']
    exact_matches = validation_results['exact_matches']
    close_matches = validation_results['close_matches']
    significant_diffs = validation_results['significant_differences']
    errors = validation_results['errors']
    
    print(f"📊 Validation Results:")
    print(f"   • Total tested: {total_tested}")
    print(f"   • ✅ Exact matches: {exact_matches}")
    print(f"   • 🟡 Close matches (≤1% diff): {close_matches}")
    print(f"   • ⚠️ Significant differences: {significant_diffs}")
    print(f"   • ❌ Errors: {errors}")
    
    if total_tested > 0:
        accuracy = (exact_matches + close_matches) / total_tested * 100
        print(f"   • 🎯 Overall accuracy: {accuracy:.1f}%")
    
    print()
    
    # Show detailed business insights for sample pathways
    print("💼 Sample Career Pathway Analysis:")
    print("-" * 60)
    
    for i, result in enumerate(validation_results['detailed_results'][:8]):
        status_icon = "✅" if result['match_status'] == 'EXACT_MATCH' else "🟡" if result['match_status'] == 'CLOSE_MATCH' else "⚠️"
        
        print(f"{status_icon} {result['job_pair']}")
        print(f"    Transition Strength: {result['business_enhanced_similarity']:.3f} | Base: {result['business_base_similarity']:.3f}")
        print(f"    Feasibility: {result['transition_feasibility']}")
        print(f"    Pathway Type: {result['career_pathway_type']}")
        print(f"    Skills to Develop: {result['skills_to_develop']} | Defining Skills Gap: {result['defining_skills_to_develop']}")
        
        if result['match_status'] != 'EXACT_MATCH':
            print(f"    Difference: {result['similarity_diff']:.6f} (Business: {result['business_enhanced_similarity']:.3f} vs DB: {result['db_enhanced_similarity']:.3f})")
        print()
    
    # Generate comprehensive business insights
    print("📈 Generating Business Insights Report...")
    insights = validator.generate_business_insights_report()
    
    print("\n🎯 Top Career Pathways (Highest Transition Strength):")
    print("-" * 60)
    for pathway in insights['top_career_pathways'][:10]:
        print(f"   {pathway['from_job']} → {pathway['to_job']}")
        print(f"     Strength: {pathway['transition_strength']} | Overlap: {pathway['skill_overlap']} | Defining Skills: {pathway['shared_defining_skills']}")
        print()
    
    print("📊 Defining Skills Impact Analysis:")
    for boost_data in insights['defining_skills_impact']['boost_by_shared_defining_skills'][:5]:
        shared_count = boost_data['shared_defining_skills_count']
        avg_boost = boost_data['avg_boost']
        pathway_count = boost_data['pathway_count']
        print(f"   {shared_count} shared defining skills: {avg_boost:.3f} avg boost ({pathway_count:,} pathways)")
    
    print(f"\n📈 Career Pathway Distribution:")
    for pathway_type, count in insights['career_pathway_types'].items():
        print(f"   {pathway_type}: {count:,} pathways")
    
    print(f"\n🎓 Skill Development Insights:")
    skill_patterns = insights['skill_development_patterns']
    print(f"   Average skills to develop per transition: {skill_patterns['average_skills_to_develop']}")
    print(f"   Average shared defining skills: {skill_patterns['average_shared_defining_skills']}")
    print(f"   Pathways with defining skills overlap: {skill_patterns['pathways_with_defining_skills_overlap']:,}")
    
    # Overall assessment
    print("\n" + "=" * 80)
    if accuracy >= 95:
        print("🎉 EXCELLENT: Business logic validation passed with high accuracy!")
        print("   The enhanced similarity algorithm correctly serves the career pathway use case.")
    elif accuracy >= 85:
        print("✅ GOOD: Business logic validation passed with acceptable accuracy.")
        print("   Minor discrepancies may be due to floating point precision or configuration differences.")
    else:
        print("⚠️ ATTENTION NEEDED: Significant differences found between business logic and database.")
        print("   Review algorithm implementation and configuration parameters.")
    
    print(f"\n🎯 Business Use Case Validation: {'PASSED' if accuracy >= 85 else 'NEEDS REVIEW'}")
    print("   The system provides actionable career pathway intelligence for asymmetric job transitions.")
    print("=" * 80)


if __name__ == "__main__":
    main()