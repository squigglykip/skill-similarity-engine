#!/usr/bin/env python3

import sqlite3

def query_job_similarities(job_id):
    """Query job similarities for a given job ID"""
    conn = sqlite3.connect('models/2025-Q3/business_context.sqlite')
    cursor = conn.cursor()
    
    # Query top similar jobs
    query = """
    SELECT 
        job_to, 
        similarity_score, 
        enhanced_similarity_score,
        shared_skills_count,
        shared_defining_skills_count
    FROM analytics_job_similarities 
    WHERE job_from = ? 
    ORDER BY enhanced_similarity_score DESC 
    LIMIT 15
    """
    
    cursor.execute(query, (job_id,))
    results = cursor.fetchall()
    
    print(f"\n=== Top Similar Jobs for {job_id} ===")
    print("=" * 80)
    print(f"{'Job To':<12} | {'Literal':<8} | {'Enhanced':<10} | {'Shared':<6} | {'Defining':<8}")
    print("-" * 80)
    
    for row in results:
        job_to, literal, enhanced, shared, defining = row
        print(f"{job_to:<12} | {literal:<8.3f} | {enhanced:<10.3f} | {shared:<6} | {defining:<8}")
    
    # Query statistics
    stats_query = """
    SELECT 
        COUNT(*) as total_comparisons,
        AVG(similarity_score) as avg_literal,
        AVG(enhanced_similarity_score) as avg_enhanced,
        MIN(similarity_score) as min_literal,
        MAX(similarity_score) as max_literal,
        MIN(enhanced_similarity_score) as min_enhanced,
        MAX(enhanced_similarity_score) as max_enhanced
    FROM analytics_job_similarities 
    WHERE job_from = ?
    """
    
    cursor.execute(stats_query, (job_id,))
    stats = cursor.fetchone()
    
    print(f"\n=== Statistics for {job_id} ===")
    print(f"Total job comparisons: {stats[0]}")
    print(f"Literal similarity - Avg: {stats[1]:.3f}, Min: {stats[3]:.3f}, Max: {stats[4]:.3f}")
    print(f"Enhanced similarity - Avg: {stats[2]:.3f}, Min: {stats[5]:.3f}, Max: {stats[6]:.3f}")
    
    conn.close()

if __name__ == "__main__":
    query_job_similarities("R0041.4")