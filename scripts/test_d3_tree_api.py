#!/usr/bin/env python3
"""
Test D3.js Tree API Queries
==========================

Quick test script to verify our SQL queries work with the database
before running the Flask app.
"""

import sqlite3
import json
from pathlib import Path

def test_tree_queries():
    """Test the SQL queries for our D3.js tree API."""
    
    # Database path
    script_dir = Path(__file__).parent
    db_path = script_dir.parent / "models" / "2025-Q2" / "business_context.sqlite"
    
    if not db_path.exists():
        print(f"❌ Database not found at: {db_path}")
        return
    
    print("🧪 Testing D3.js Tree API Queries")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Test 1: Get job families
        print("\n1️⃣ Testing Job Families Query:")
        cursor.execute("""
            SELECT JobFamily, COUNT(*) as job_count
            FROM jobs 
            WHERE JobFamily IS NOT NULL
            GROUP BY JobFamily
            ORDER BY job_count DESC
            LIMIT 5
        """)
        families = cursor.fetchall()
        print(f"   Found {len(families)} job families:")
        for family in families:
            print(f"   • {family['JobFamily']}: {family['job_count']} jobs")
        
        # Test 2: Get tree data for specific family
        test_family = "Data & Analytics"
        print(f"\n2️⃣ Testing Tree Data Query for '{test_family}':")
        
        # Get jobs in family
        cursor.execute("""
            SELECT JobProfileID, JobProfile, JobFamily
            FROM jobs 
            WHERE JobFamily = ?
            ORDER BY JobProfile
            LIMIT 5
        """, (test_family,))
        jobs = cursor.fetchall()
        print(f"   Found {len(jobs)} jobs in {test_family}:")
        
        tree_data = {
            'name': test_family,
            'type': 'family',
            'children': []
        }
        
        for job in jobs:
            print(f"   • {job['JobProfile']} ({job['JobProfileID']})")
            
            # Get similar jobs
            cursor.execute("""
                SELECT j2.JobProfileID, j2.JobProfile, j2.JobFamily, 
                       js.similarity_score
                FROM job_similarities js
                JOIN jobs j2 ON js.job_to = j2.JobProfileID
                WHERE js.job_from = ?
                  AND js.similarity_score >= 0.6
                  AND js.job_from != js.job_to
                ORDER BY js.similarity_score DESC
                LIMIT 3
            """, (job['JobProfileID'],))
            
            similar_jobs = cursor.fetchall()
            print(f"     → Found {len(similar_jobs)} similar jobs (60%+ similarity)")
            
            job_node = {
                'name': job['JobProfile'],
                'type': 'job',
                'id': job['JobProfileID'],
                'family': job['JobFamily'],
                'children': []
            }
            
            for similar_job in similar_jobs:
                print(f"       - {similar_job['JobProfile']} ({similar_job['similarity_score']:.1%})")
                similar_node = {
                    'name': similar_job['JobProfile'],
                    'type': 'similar_job',
                    'id': similar_job['JobProfileID'],
                    'family': similar_job['JobFamily'],
                    'similarity': round(similar_job['similarity_score'], 3),
                    'size': int(similar_job['similarity_score'] * 100)
                }
                job_node['children'].append(similar_node)
            
            tree_data['children'].append(job_node)
        
        # Test 3: Show sample JSON structure
        print(f"\n3️⃣ Sample JSON Tree Structure:")
        print(json.dumps(tree_data, indent=2)[:500] + "..." if len(json.dumps(tree_data)) > 500 else json.dumps(tree_data, indent=2))
        
        # Test 4: Database schema validation
        print(f"\n4️⃣ Database Schema Validation:")
        
        # Check if we can access all required tables
        tables = ['jobs', 'job_similarities', 'skills', 'job_skills', 'positions']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            count = cursor.fetchone()['count']
            print(f"   ✅ {table}: {count:,} records")
        
        # Test similarity score distribution for the family
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN js.similarity_score >= 0.8 THEN 'High (80%+)'
                    WHEN js.similarity_score >= 0.6 THEN 'Medium (60-80%)'
                    WHEN js.similarity_score >= 0.4 THEN 'Low (40-60%)'
                    ELSE 'Very Low (<40%)'
                END as similarity_range,
                COUNT(*) as count
            FROM job_similarities js
            JOIN jobs j1 ON js.job_from = j1.JobProfileID
            WHERE j1.JobFamily = ?
            GROUP BY similarity_range
            ORDER BY MIN(js.similarity_score) DESC
        """, (test_family,))
        
        sim_dist = cursor.fetchall()
        print(f"\n   Similarity Distribution for {test_family}:")
        for dist in sim_dist:
            print(f"   • {dist['similarity_range']}: {dist['count']:,} pairs")
        
        conn.close()
        
        print(f"\n✅ All tests passed! Ready to run Flask app.")
        print(f"📁 Database: {db_path}")
        print(f"🌐 Run: python run_webapp.py")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_tree_queries() 