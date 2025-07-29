#!/usr/bin/env python3
"""Real-world test of unified similarity algorithm with defining skills boost."""

import sys
import os
import sqlite3
import tempfile
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from skill_similarity_engine.similarity.asymmetric import AsymmetricCoverageCalculator
from skill_similarity_engine.models.jobs import Job, JobArchitecture, JobLevel
from skill_similarity_engine.business_context.schema_builder import SchemaBuilder
from skill_similarity_engine.config.architectural_config_manager import get_config_manager
import pandas as pd

def test_unified_vs_basic_similarity():
    """Test the unified similarity algorithm with defining skills boost vs basic Jaccard."""
    print("🧪 Testing Unified Similarity Algorithm (Defining Skills Boost)")
    print("=" * 60)
    
    try:
        # Create sample jobs that demonstrate the defining skills boost
        print("📊 Creating sample job architecture...")
        jobs = {
            'data_scientist': Job(
                job_id='data_scientist',
                title='Senior Data Scientist',
                department='Analytics',
                level=JobLevel.SENIOR,
                skills={
                    'Python': 5,
                    'Machine Learning': 5,
                    'Statistics': 5,
                    'Deep Learning': 4,           # Rare skill
                    'Advanced_NLP': 4,            # Very rare skill  
                    'SQL': 3                      # Common skill
                }
            ),
            'ml_engineer': Job(
                job_id='ml_engineer',
                title='ML Engineer',
                department='Engineering',
                level=JobLevel.SENIOR,
                skills={
                    'Python': 5,
                    'Machine Learning': 5,
                    'MLOps': 4,
                    'Deep Learning': 5,           # Same rare skill
                    'Advanced_NLP': 4,            # Same very rare skill
                    'Kubernetes': 3               # Different common skill
                }
            )
        }
        
        job_architecture = JobArchitecture(jobs=jobs)
        
        # Create skill universe that makes some skills rare and others common
        skill_universe_df = pd.DataFrame({
            'Skill_ID': ['skill_001', 'skill_002', 'skill_003', 'skill_004', 'skill_005', 'skill_006', 'skill_007'],
            'Skill_Name': ['Python', 'Machine Learning', 'Statistics', 'Deep Learning', 'Advanced_NLP', 'SQL', 'Kubernetes'],
            'Category': ['Technical', 'Technical', 'Technical', 'Technical', 'Technical', 'Technical', 'Technical'],
            'SkillType': ['Programming', 'AI/ML', 'Analytics', 'AI/ML', 'AI/ML', 'Database', 'DevOps'],
            'prevalence_percentage': [85.0, 45.0, 60.0, 8.5, 2.3, 75.0, 25.0],  # Advanced_NLP and Deep Learning are rare
            'rarity_category': ['Universal', 'Common', 'Common', 'Rare', 'Rare', 'Universal', 'Common']
        })
        
        print(f"✅ Created sample data:")
        print(f"   → Data Scientist skills: {set(jobs['data_scientist'].skills.keys())}")
        print(f"   → ML Engineer skills: {set(jobs['ml_engineer'].skills.keys())}")
        print(f"   → Skill universe: {len(skill_universe_df)} skills with rarity data")
        
        # Show skill rarity breakdown
        print(f"\n📊 Skill Rarity Breakdown:")
        for _, row in skill_universe_df.iterrows():
            print(f"   → {row['Skill_Name']}: {row['prevalence_percentage']}% prevalence ({row['rarity_category']})")
        
        # Test basic similarity using existing method
        print(f"\n📊 Testing basic Jaccard similarity...")
        basic_calculator = AsymmetricCoverageCalculator(job_architecture)
        basic_result = basic_calculator.calculate_symmetric_similarity('data_scientist', 'ml_engineer')
        print(f"Basic Jaccard Similarity: {basic_result:.4f}")
        
        # Test unified similarity algorithm
        print(f"\n🧠 Testing unified similarity algorithm...")
        unified_calculator = AsymmetricCoverageCalculator(job_architecture, skill_universe_df)
        
        # Get skills as sets for the unified method
        ds_skills = set(jobs['data_scientist'].skills.keys())
        ml_skills = set(jobs['ml_engineer'].skills.keys())
        
        unified_result = unified_calculator.calculate_rarity_weighted_similarity(ds_skills, ml_skills)
        
        print(f"Unified Similarity Results:")
        print(f"   → Basic component: {unified_result['basic_similarity']:.4f}")
        print(f"   → Enhanced similarity: {unified_result['enhanced_similarity']:.4f}")
        print(f"   → Shared skills: {unified_result['shared_skills']}")
        print(f"   → Shared defining skills: {unified_result['shared_defining_skills']}")
        print(f"   → Shared defining skills count: {unified_result['shared_defining_skills_count']}")
        print(f"   → Defining skill boost: {unified_result['defining_skill_boost']:.4f}")
        
        # Show which skills are considered defining for each job
        print(f"\n🎯 Defining Skills Analysis:")
        ds_defining = unified_calculator._get_defining_skills_for_skillset(ds_skills)
        ml_defining = unified_calculator._get_defining_skills_for_skillset(ml_skills)
        print(f"   → Data Scientist defining skills (top 20% rarest): {ds_defining}")
        print(f"   → ML Engineer defining skills (top 20% rarest): {ml_defining}")
        
        # Validate the algorithm logic using configuration values
        print(f"\n🔍 Algorithm Validation:")
        shared_skills = ds_skills & ml_skills
        all_defining = ds_defining | ml_defining
        shared_defining = [skill for skill in shared_skills if skill in all_defining]
        
        # Get the multiplier from configuration (no hardcoded values)
        config = unified_calculator.rarity_weighted_config
        gentle_multiplier = config['gentle_multiplier']
        
        expected_boost = len(shared_defining) * (gentle_multiplier - 1.0)
        expected_enhanced = basic_result * (1.0 + expected_boost)
        expected_enhanced = min(1.0, expected_enhanced)  # Cap at 1.0
        
        print(f"   → Configuration multiplier: {gentle_multiplier}")
        print(f"   → Expected defining skills boost: {expected_boost:.4f}")
        print(f"   → Expected enhanced similarity: {expected_enhanced:.4f}")
        print(f"   → Actual enhanced similarity: {unified_result['enhanced_similarity']:.4f}")
        print(f"   → Match: {'✅' if abs(expected_enhanced - unified_result['enhanced_similarity']) < 0.0001 else '❌'}")
        
        # Validate improvement
        improvement = unified_result['enhanced_similarity'] - basic_result
        improvement_pct = (improvement / basic_result) * 100 if basic_result > 0 else 0
        
        print(f"\n📈 Improvement Analysis:")
        print(f"   → Absolute improvement: {improvement:.4f}")
        print(f"   → Percentage improvement: {improvement_pct:.2f}%")
        print(f"   → Number of shared defining skills: {len(shared_defining)}")
        print(f"   → Shared defining skills: {shared_defining}")
        
        # The algorithm should show improvement when there are shared defining (rare) skills
        if len(shared_defining) > 0 and improvement > 0:
            print("✅ Unified similarity shows expected improvement with shared defining skills")
            return True
        elif len(shared_defining) == 0 and improvement == 0:
            print("✅ Unified similarity correctly shows no improvement when no shared defining skills")
            return True
        else:
            print("❌ Unexpected algorithm behavior")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

def test_unified_config_loading():
    """Test that the unified similarity configuration loads correctly."""
    print("\n🧪 Testing Unified Similarity Configuration Loading")
    print("=" * 50)
    
    try:
        config_manager = get_config_manager()
        
        # Test loading the configuration without hardcoded defaults
        config = config_manager.get_nested_value('similarity', 'rarity_weighted_algorithms')
        
        if not config:
            print("❌ Configuration section 'similarity.rarity_weighted_algorithms' not found")
            return False
        
        print(f"Unified Similarity Configuration:")
        print(f"   → Enabled: {config.get('enabled', 'Not specified')}")
        print(f"   → Defining skills percentile: {config.get('defining_skills_percentile', 'Not specified')}")
        print(f"   → Gentle multiplier: {config.get('gentle_multiplier', 'Not specified')}")
        print(f"   → Rarity thresholds: {config.get('rarity_thresholds', 'Not specified')}")
        
        # Validate that all required parameters are present (no defaults)
        required_params = ['defining_skills_percentile', 'gentle_multiplier', 'rarity_thresholds']
        missing_params = [param for param in required_params if param not in config]
        
        if missing_params:
            print(f"❌ Missing required configuration parameters: {missing_params}")
            return False
        
        # Validate parameter types and ranges
        percentile = config['defining_skills_percentile']
        multiplier = config['gentle_multiplier']
        
        if not isinstance(percentile, (int, float)) or not (1 <= percentile <= 100):
            print(f"❌ defining_skills_percentile must be between 1 and 100, got: {percentile}")
            return False
        
        if not isinstance(multiplier, (int, float)) or multiplier <= 1.0:
            print(f"❌ gentle_multiplier must be greater than 1.0, got: {multiplier}")
            return False
        
        if not isinstance(config['rarity_thresholds'], dict):
            print(f"❌ rarity_thresholds must be a dictionary, got: {type(config['rarity_thresholds'])}")
            return False
        
        print("✅ Unified similarity configuration loaded and validated successfully")
        print("✅ All parameters are configuration-driven with no hardcoded defaults")
        return True
            
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        return False

def test_database_schema_extensions():
    """Test that database schema includes the necessary columns for unified similarity."""
    print("\n🧪 Testing Database Schema Extensions")
    print("=" * 50)
    
    try:
        # Create temporary database for testing
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_file:
            test_db_path = tmp_file.name
        
        print(f"📁 Creating test database: {test_db_path}")
        
        # Create schema
        schema_builder = SchemaBuilder(test_db_path)
        schema_builder.create_schema()
        
        # Check schema
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        
        try:
            # Check job_similarities table columns
            cursor.execute("PRAGMA table_info(job_similarities)")
            columns = [row[1] for row in cursor.fetchall()]
            
            print(f"📊 job_similarities table columns: {len(columns)} total")
            
            # Check for required columns
            required_columns = [
                'enhanced_similarity_score',
                'rarity_weighted_score', 
                'shared_defining_skills_count',
                'defining_skill_boost'
            ]
            
            missing_columns = []
            for col in required_columns:
                if col in columns:
                    print(f"   ✅ {col}")
                else:
                    print(f"   ❌ {col} (missing)")
                    missing_columns.append(col)
            
            # Check for new tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_new_tables = [
                'skill_rarity_analysis',
                'job_defining_skills'
            ]
            
            print(f"\n📊 Enhanced similarity tables:")
            missing_tables = []
            for table in expected_new_tables:
                if table in tables:
                    print(f"   ✅ {table}")
                else:
                    print(f"   ❌ {table} (missing)")
                    missing_tables.append(table)
            
            if not missing_columns and not missing_tables:
                print("✅ All unified similarity database schema elements present")
                return True
            else:
                print(f"❌ Missing schema elements: {missing_columns + missing_tables}")
                return False
        finally:
            conn.close()
            # Clean up test database
            try:
                if test_db_path and Path(test_db_path).exists():
                    os.unlink(test_db_path)
            except (OSError, FileNotFoundError):
                pass  # File may not exist or already deleted
                
    except Exception as e:
        print(f"❌ Database schema test failed: {e}")
        return False

def main():
    """Run all unified similarity algorithm tests."""
    print("🚀 Unified Similarity Algorithm Testing Suite")
    print("=" * 70)
    print("Testing the single, unified algorithm with defining skills boost")
    print("Expected: Improvement when jobs share rare (defining) skills")
    print("Algorithm: Basic Jaccard + configuration-driven boost per shared defining skill")
    print("All parameters loaded from configuration (no hardcoded values)")
    print("=" * 70)
    
    tests = [
        ("Unified vs Basic Similarity", test_unified_vs_basic_similarity),
        ("Configuration Loading", test_unified_config_loading),
        ("Database Schema Extensions", test_database_schema_extensions)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name}...")
        results[test_name] = test_func()
    
    # Summary
    print("\n📊 TEST RESULTS SUMMARY")
    print("=" * 30)
    passed = sum(results.values())
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Unified similarity algorithm is working correctly.")
        print("📈 The system uses the single, empirically-tuned algorithm from skill_intelligence_engine.py")
        print("🎯 Algorithm: Basic Jaccard + configuration-driven boost per shared defining skill")
        print("✅ All parameters are externalized to configuration following architectural philosophy")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    main() 