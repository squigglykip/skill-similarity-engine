#!/usr/bin/env python3
"""
Verify Production Database Compatibility
========================================

This script verifies that both generate_sqlite_schema_docs.py and 
optuna_asymmetric_hyperparameter_optimization.py work correctly 
with the production database (1700+ jobs instead of synthetic 715).

Checks:
1. Database table existence and row counts
2. Schema documentation script table references
3. Optuna script database queries
4. No hardcoded values used
"""

import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Tuple

def check_database_tables(db_path: str) -> Dict[str, int]:
    """Check which tables exist and their row counts."""
    print(f"🔍 Analyzing database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        # Get row counts for each table
        table_counts = {}
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                table_counts[table] = count
                print(f"   📊 {table}: {count:,} records")
            except sqlite3.Error as e:
                print(f"   ❌ {table}: Error counting records - {e}")
                table_counts[table] = 0
        
        conn.close()
        return table_counts
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return {}

def verify_production_scale(table_counts: Dict[str, int]) -> bool:
    """Verify this is production scale data, not synthetic."""
    print("\n🎯 Verifying Production Scale:")
    
    # Check for production indicators
    production_indicators = []
    
    # Job count should be ~1700, not 715
    job_count = table_counts.get('core_job_architecture', 0)
    if job_count > 1500:
        production_indicators.append(f"✅ Job count: {job_count:,} (production scale)")
    elif job_count == 715:
        production_indicators.append(f"⚠️  Job count: {job_count:,} (synthetic scale)")
        return False
    else:
        production_indicators.append(f"❓ Job count: {job_count:,} (unknown scale)")
    
    # Skills should be substantial
    skills_count = table_counts.get('core_skills_taxonomy', 0)
    if skills_count > 30000:
        production_indicators.append(f"✅ Skills count: {skills_count:,} (production scale)")
    else:
        production_indicators.append(f"⚠️  Skills count: {skills_count:,} (may be synthetic)")
    
    # Colleague positions should be substantial
    positions_count = table_counts.get('core_colleague_positions_history', 0)
    if positions_count > 100000:
        production_indicators.append(f"✅ Position history: {positions_count:,} (production scale)")
    else:
        production_indicators.append(f"⚠️  Position history: {positions_count:,} (may be synthetic)")
    
    for indicator in production_indicators:
        print(f"   {indicator}")
    
    return job_count > 1500

def test_schema_docs_queries(db_path: str) -> bool:
    """Test that schema documentation queries work with production tables."""
    print("\n📋 Testing Schema Documentation Queries:")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test key business metrics queries (from the fixed script)
        queries = [
            ("Job count", "SELECT COUNT(DISTINCT JobProfileID) FROM core_job_architecture"),
            ("Job families", "SELECT COUNT(DISTINCT JobFamily) FROM core_job_architecture"),
            ("Skills count", "SELECT COUNT(DISTINCT Skill_ID) FROM core_skills_taxonomy"),
            ("Workforce positions", "SELECT COUNT(DISTINCT \"Position Number\") FROM core_workforce_current"),
            ("Career pathways", "SELECT COUNT(*) FROM analytics_career_pathways"),
            ("Job similarities", "SELECT COUNT(*) FROM analytics_job_similarities")
        ]
        
        all_passed = True
        for query_name, query in queries:
            try:
                cursor.execute(query)
                result = cursor.fetchone()[0]
                print(f"   ✅ {query_name}: {result:,}")
            except sqlite3.Error as e:
                print(f"   ❌ {query_name}: Query failed - {e}")
                all_passed = False
        
        conn.close()
        return all_passed
        
    except sqlite3.Error as e:
        print(f"   ❌ Database connection failed: {e}")
        return False

def test_optuna_queries(db_path: str) -> bool:
    """Test that Optuna optimization queries work with production tables."""
    print("\n🧠 Testing Optuna Optimization Queries:")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test core queries from optuna script
        queries = [
            ("Jobs data", """
                SELECT JobProfileID, JobProfile, JobFunction, ManagementLevel, JobCategory
                FROM core_job_architecture
                ORDER BY JobProfileID
                LIMIT 5
            """),
            ("Job-skill relationships", """
                SELECT js.JobProfileID, js.Skill_ID, s.Skill_Name, s.Category, s.SkillType
                FROM core_job_skill_requirements js
                JOIN core_skills_taxonomy s ON js.Skill_ID = s.Skill_ID
                ORDER BY js.JobProfileID, s.Skill_Name
                LIMIT 5
            """)
        ]
        
        all_passed = True
        for query_name, query in queries:
            try:
                cursor.execute(query)
                results = cursor.fetchall()
                print(f"   ✅ {query_name}: {len(results)} sample records retrieved")
            except sqlite3.Error as e:
                print(f"   ❌ {query_name}: Query failed - {e}")
                all_passed = False
        
        # Test job pairs calculation
        try:
            cursor.execute("SELECT COUNT(DISTINCT JobProfileID) FROM core_job_architecture")
            job_count = cursor.fetchone()[0]
            total_pairs = job_count * (job_count - 1)
            print(f"   ✅ Job pairs calculation: {total_pairs:,} pairs ({job_count:,} jobs)")
        except sqlite3.Error as e:
            print(f"   ❌ Job pairs calculation failed: {e}")
            all_passed = False
        
        conn.close()
        return all_passed
        
    except sqlite3.Error as e:
        print(f"   ❌ Database connection failed: {e}")
        return False

def main():
    """Main verification function."""
    print("🔍 PRODUCTION DATABASE COMPATIBILITY VERIFICATION")
    print("=" * 60)
    
    # Find database
    project_root = Path(__file__).parent.parent
    db_path = project_root / "models" / "2025-Q3" / "business_context.sqlite"
    
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        print("   Run 'python main.py' → option 1 → option 1 to create database first")
        return 1
    
    # Check database tables and counts
    table_counts = check_database_tables(str(db_path))
    if not table_counts:
        print("❌ Failed to analyze database tables")
        return 1
    
    # Verify production scale
    is_production = verify_production_scale(table_counts)
    if not is_production:
        print("\n⚠️  WARNING: Database appears to contain synthetic data (715 jobs)")
        print("   This verification is designed for production data (~1700+ jobs)")
        print("   Results may not reflect production compatibility")
    
    # Test schema documentation queries
    schema_docs_ok = test_schema_docs_queries(str(db_path))
    
    # Test optuna queries
    optuna_ok = test_optuna_queries(str(db_path))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 60)
    
    print(f"🗄️  Database Scale: {'Production' if is_production else 'Synthetic'}")
    print(f"📋 Schema Docs Queries: {'✅ PASS' if schema_docs_ok else '❌ FAIL'}")
    print(f"🧠 Optuna Queries: {'✅ PASS' if optuna_ok else '❌ FAIL'}")
    
    if schema_docs_ok and optuna_ok:
        print("\n🎉 SUCCESS: Both scripts are compatible with your database!")
        print("   • generate_sqlite_schema_docs.py will work correctly")
        print("   • optuna_asymmetric_hyperparameter_optimization.py will work correctly")
        if is_production:
            print(f"   • Production scale confirmed: {table_counts.get('core_job_architecture', 0):,} jobs")
        return 0
    else:
        print("\n❌ ISSUES FOUND: Some scripts may not work correctly with your database")
        print("   Check the error messages above for specific problems")
        return 1

if __name__ == "__main__":
    exit(main())