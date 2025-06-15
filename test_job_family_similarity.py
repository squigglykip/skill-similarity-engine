#!/usr/bin/env python3
"""
Test script to debug job family similarity analysis
"""

import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

def main():
    # Connect to database
    db_path = "models/2025-Q2/business_context.sqlite"
    print(f"🔍 Connecting to database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return

    # Step 1: Check basic table structures
    print("\n" + "="*60)
    print("📊 STEP 1: DATABASE STRUCTURE ANALYSIS")
    print("="*60)
    
    # Check jobs table
    jobs_count = pd.read_sql_query("SELECT COUNT(*) as count FROM jobs", conn).iloc[0]['count']
    print(f"Jobs table: {jobs_count:,} records")
    
    # Check job_similarities table
    similarities_count = pd.read_sql_query("SELECT COUNT(*) as count FROM job_similarities", conn).iloc[0]['count']
    print(f"Job similarities table: {similarities_count:,} records")
    
    # Check JobFamily data in jobs table
    job_families = pd.read_sql_query("""
        SELECT JobFamily, COUNT(*) as job_count 
        FROM jobs 
        WHERE JobFamily IS NOT NULL 
        GROUP BY JobFamily 
        ORDER BY job_count DESC
    """, conn)
    
    print(f"\n📋 Job Families in jobs table:")
    print(f"   • Total families: {len(job_families)}")
    for i, row in job_families.head(10).iterrows():
        print(f"   • {row['JobFamily']}: {row['job_count']} jobs")
    
    # Step 2: Check data quality in job_similarities
    print("\n" + "="*60)
    print("📊 STEP 2: JOB SIMILARITIES DATA QUALITY")
    print("="*60)
    
    # Check shared_skills_count data
    shared_skills_stats = pd.read_sql_query("""
        SELECT 
            COUNT(*) as total_records,
            COUNT(shared_skills_count) as records_with_shared_skills,
            AVG(shared_skills_count) as avg_shared_skills,
            MIN(shared_skills_count) as min_shared_skills,
            MAX(shared_skills_count) as max_shared_skills
        FROM job_similarities
    """, conn)
    
    print("Shared skills data:")
    for col in shared_skills_stats.columns:
        val = shared_skills_stats.iloc[0][col]
        if pd.isna(val):
            print(f"   • {col}: NULL")
        elif isinstance(val, float):
            print(f"   • {col}: {val:.2f}")
        else:
            print(f"   • {col}: {val:,}")
    
    # Step 3: Test the JOIN operation
    print("\n" + "="*60)
    print("📊 STEP 3: JOIN OPERATION TESTING")
    print("="*60)
    
    # Test basic JOIN without filters
    basic_join = pd.read_sql_query("""
        SELECT 
            COUNT(*) as total_joined_records,
            COUNT(j1.JobFamily) as records_with_family1,
            COUNT(j2.JobFamily) as records_with_family2,
            COUNT(CASE WHEN j1.JobFamily IS NOT NULL AND j2.JobFamily IS NOT NULL THEN 1 END) as records_with_both_families
        FROM job_similarities js
        LEFT JOIN jobs j1 ON js.job_from = j1.JobProfileID
        LEFT JOIN jobs j2 ON js.job_to = j2.JobProfileID
    """, conn)
    
    print("JOIN operation results:")
    for col in basic_join.columns:
        val = basic_join.iloc[0][col]
        print(f"   • {col}: {val:,}")
    
    # Step 4: Test with shared_skills_count filter
    print("\n" + "="*60)
    print("📊 STEP 4: SHARED SKILLS FILTER TESTING")
    print("="*60)
    
    with_shared_skills = pd.read_sql_query("""
        SELECT 
            COUNT(*) as records_with_shared_skills,
            COUNT(CASE WHEN j1.JobFamily IS NOT NULL AND j2.JobFamily IS NOT NULL THEN 1 END) as records_with_both_families_and_skills
        FROM job_similarities js
        LEFT JOIN jobs j1 ON js.job_from = j1.JobProfileID
        LEFT JOIN jobs j2 ON js.job_to = j2.JobProfileID
        WHERE js.shared_skills_count IS NOT NULL
    """, conn)
    
    print("With shared_skills_count filter:")
    for col in with_shared_skills.columns:
        val = with_shared_skills.iloc[0][col]
        print(f"   • {col}: {val:,}")
    
    # Step 5: Try the query without the shared_skills_count filter
    print("\n" + "="*60)
    print("📊 STEP 5: FAMILY SIMILARITY WITHOUT SHARED SKILLS FILTER")
    print("="*60)
    
    try:
        family_similarity_no_filter = pd.read_sql_query("""
            SELECT 
                j1.JobFamily as family1,
                j2.JobFamily as family2,
                AVG(js.similarity_score) as avg_similarity,
                COUNT(js.similarity_score) as pair_count
            FROM job_similarities js
            LEFT JOIN jobs j1 ON js.job_from = j1.JobProfileID
            LEFT JOIN jobs j2 ON js.job_to = j2.JobProfileID
            WHERE j1.JobFamily IS NOT NULL AND j2.JobFamily IS NOT NULL
            GROUP BY j1.JobFamily, j2.JobFamily
            HAVING COUNT(js.similarity_score) >= 1
            ORDER BY avg_similarity DESC
            LIMIT 20
        """, conn)
        
        print(f"✅ Query successful: {len(family_similarity_no_filter)} family combinations found")
        print("\nTop 10 family combinations:")
        for i, row in family_similarity_no_filter.head(10).iterrows():
            print(f"   • {row['family1']} ↔ {row['family2']}")
            print(f"     Avg Similarity: {row['avg_similarity']:.3f} | Pairs: {row['pair_count']}")
            
    except Exception as e:
        print(f"❌ Query failed: {e}")
    
    # Step 6: Try with shared_skills_count filter but lower threshold
    print("\n" + "="*60)
    print("📊 STEP 6: FAMILY SIMILARITY WITH SHARED SKILLS FILTER (LOWER THRESHOLD)")
    print("="*60)
    
    try:
        family_similarity_with_filter = pd.read_sql_query("""
            SELECT 
                j1.JobFamily as family1,
                j2.JobFamily as family2,
                AVG(js.similarity_score) as avg_similarity,
                COUNT(js.similarity_score) as pair_count,
                AVG(js.shared_skills_count) as avg_shared_skills
            FROM job_similarities js
            LEFT JOIN jobs j1 ON js.job_from = j1.JobProfileID
            LEFT JOIN jobs j2 ON js.job_to = j2.JobProfileID
            WHERE j1.JobFamily IS NOT NULL AND j2.JobFamily IS NOT NULL
                AND js.shared_skills_count IS NOT NULL
            GROUP BY j1.JobFamily, j2.JobFamily
            HAVING COUNT(js.similarity_score) >= 1
            ORDER BY avg_similarity DESC
            LIMIT 20
        """, conn)
        
        print(f"✅ Query successful: {len(family_similarity_with_filter)} family combinations found")
        print("\nTop 10 family combinations (with shared skills data):")
        for i, row in family_similarity_with_filter.head(10).iterrows():
            print(f"   • {row['family1']} ↔ {row['family2']}")
            print(f"     Avg Similarity: {row['avg_similarity']:.3f} | Pairs: {row['pair_count']} | Avg Shared Skills: {row['avg_shared_skills']:.1f}")
            
    except Exception as e:
        print(f"❌ Query failed: {e}")
    
    # Step 7: Sample some actual data
    print("\n" + "="*60)
    print("📊 STEP 7: SAMPLE DATA INSPECTION")
    print("="*60)
    
    sample_data = pd.read_sql_query("""
        SELECT 
            js.job_from,
            js.job_to,
            js.similarity_score,
            js.shared_skills_count,
            j1.JobFamily as family1,
            j2.JobFamily as family2,
            j1.JobProfile as job1_name,
            j2.JobProfile as job2_name
        FROM job_similarities js
        LEFT JOIN jobs j1 ON js.job_from = j1.JobProfileID
        LEFT JOIN jobs j2 ON js.job_to = j2.JobProfileID
        WHERE j1.JobFamily IS NOT NULL AND j2.JobFamily IS NOT NULL
        ORDER BY js.similarity_score DESC
        LIMIT 10
    """, conn)
    
    print("Sample high-similarity job pairs:")
    for i, row in sample_data.iterrows():
        print(f"   • {row['job1_name']} ({row['family1']})")
        print(f"     ↔ {row['job2_name']} ({row['family2']})")
        print(f"     Similarity: {row['similarity_score']:.3f}, Shared Skills: {row['shared_skills_count']}")
        print()
    
    conn.close()
    print("\n✅ Analysis complete!")

if __name__ == "__main__":
    main() 