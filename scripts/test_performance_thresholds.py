#!/usr/bin/env python3
"""
Performance Testing Script for Career Pathway Query Thresholds
Tests various parameter combinations to determine when warnings should appear.
"""

import sqlite3
import time
import sys
import os

# Add the src directory to the Python path if not installed as a package
src_path = os.path.join(os.path.dirname(__file__), 'src')
if os.path.exists(src_path) and src_path not in sys.path:
    sys.path.insert(0, src_path)

# Use the exact same SQL query as the Flask app
CAREER_TREE_QUERY = """
WITH RECURSIVE tree_builder AS (
    -- Level 0: Root nodes (selected starting jobs)
    SELECT 
        'root' as node_type,
        j.JobProfileID as id,
        j.JobProfile as name,
        NULL as parent_id,
        0 as level,
        j.JobFamily as category,
        1.0 as similarity_score,
        'starting_role' as career_move_type,
        0.0 as difficulty_score,
        0 as shared_skills_count,
        0 as children_count,
        j.JobProfileID as root_job_id
    FROM jobs j
    WHERE j.JobProfileID IN ({job_placeholders})
    
    UNION ALL
    
    -- Recursive expansion: Get direct pathways from each node
    SELECT 
        'similar_job' as node_type,
        cp.target_job_id as id,
        j.JobProfile as name,
        cp.source_job_id as parent_id,
        tb.level + 1 as level,
        j.JobFamily as category,
        cp.similarity_score,
        cp.career_move_type,
        cp.difficulty_score,
        cp.shared_skills_count,
        0 as children_count,  -- Will be calculated post-query
        tb.root_job_id
    FROM tree_builder tb
    JOIN career_pathways cp ON tb.id = cp.source_job_id
    JOIN jobs j ON cp.target_job_id = j.JobProfileID
    WHERE cp.similarity_score >= ?  -- similarity_threshold (param 2)
      AND tb.level < ?  -- max_depth (param 3) 
      AND cp.similarity_rank <= ?   -- max_results (param 4)
      AND cp.target_job_id != tb.root_job_id  -- Don't go back to root
      AND cp.target_job_id != tb.id  -- Don't self-reference
)
SELECT DISTINCT
    node_type,
    id,
    name,
    parent_id,
    level,
    category,
    similarity_score,
    career_move_type,
    difficulty_score,
    shared_skills_count,
    children_count
FROM tree_builder tb
WHERE tb.level = 0  -- Always include root nodes
   OR (
       -- Optimized organizational filters - only check if filters are actually set
       (? = '' OR tb.id IN (SELECT JobProfileID FROM positions WHERE Division = ?))
       AND (? = '' OR tb.id IN (SELECT JobProfileID FROM positions WHERE "Business_Unit" = ?))
       AND (? = '' OR tb.id IN (SELECT JobProfileID FROM positions WHERE Location = ?))
       AND (? = '' OR tb.id IN (SELECT JobProfileID FROM positions WHERE Rg = ?))
   )
ORDER BY level, similarity_score DESC, name;
"""

def test_query_performance():
    """Test various parameter combinations to determine performance thresholds."""
    
    # Connect to database
    db_path = os.path.join('models', '2025-Q2', 'business_context.sqlite')
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    try:
        # Use the direct query
        tree_query = CAREER_TREE_QUERY
        
        # Test job - Data Scientist Director (known to have good pathways)
        test_job_id = 'R0276.1'
        job_placeholders = '?'
        tree_query = tree_query.replace('{job_placeholders}', job_placeholders)
        
        # Define test parameter ranges
        test_cases = [
            # Format: (similarity_threshold, max_depth, max_results, description)
            (0.0, 3, 6, "Current default"),
            (0.0, 4, 6, "Slightly deeper"),
            (0.0, 5, 6, "Deep tree"),
            (0.0, 6, 6, "Very deep tree"),
            (0.0, 7, 6, "Extreme depth"),
            
            (0.0, 3, 8, "Higher results"),
            (0.0, 3, 10, "High results"),
            (0.0, 3, 12, "Max results"),
            
            (0.0, 5, 8, "Deep + high results"),
            (0.0, 5, 10, "Deep + very high results"),
            (0.0, 5, 12, "Deep + max results"),
            
            (0.0, 7, 8, "Extreme depth + high results"),
            (0.0, 7, 10, "Extreme depth + very high results"),
            (0.0, 7, 12, "Extreme depth + max results"),
            
            # Test with higher similarity thresholds
            (0.4, 7, 12, "High similarity + extreme params"),
            (0.6, 7, 12, "Very high similarity + extreme params"),
        ]
        
        print("🚀 Starting Performance Testing for Career Pathway Queries")
        print("=" * 80)
        print(f"{'Description':<35} {'Depth':<6} {'Results':<8} {'Similarity':<10} {'Time (s)':<10} {'Nodes':<8} {'Status'}")
        print("-" * 80)
        
        results = []
        
        for similarity_threshold, max_depth, max_results, description in test_cases:
            # Parameters match Flask app exactly: [job_id, similarity_threshold, max_depth, max_results, org_filters...]
            # The query expects: job_id, similarity_threshold, max_depth, max_results, division, division, business_unit, business_unit, location, location, region, region
            params = [test_job_id, similarity_threshold, max_depth, max_results, '', '', '', '', '', '', '', '']
            
            try:
                start_time = time.time()
                query_results = conn.execute(tree_query, params).fetchall()
                end_time = time.time()
                
                execution_time = end_time - start_time
                node_count = len(query_results)
                
                # Determine status based on performance
                if execution_time < 2:
                    status = "🟢 Fast"
                elif execution_time < 5:
                    status = "🟡 Moderate"
                elif execution_time < 10:
                    status = "🟠 Slow"
                else:
                    status = "🔴 Very Slow"
                
                print(f"{description:<35} {max_depth:<6} {max_results:<8} {similarity_threshold*100:>6.0f}%   {execution_time:>7.2f}   {node_count:<8} {status}")
                
                results.append({
                    'description': description,
                    'similarity_threshold': similarity_threshold,
                    'max_depth': max_depth,
                    'max_results': max_results,
                    'execution_time': execution_time,
                    'node_count': node_count,
                    'status': status
                })
                
            except Exception as e:
                print(f"{description:<35} {max_depth:<6} {max_results:<8} {similarity_threshold*100:>6.0f}%   ERROR: {str(e)[:20]}...")
                results.append({
                    'description': description,
                    'similarity_threshold': similarity_threshold,
                    'max_depth': max_depth,
                    'max_results': max_results,
                    'execution_time': None,
                    'node_count': None,
                    'status': "❌ Error"
                })
        
        print("-" * 80)
        
        # Analyze results and suggest thresholds
        print("\n📊 Performance Analysis:")
        
        slow_queries = [r for r in results if r['execution_time'] and r['execution_time'] > 5]
        very_slow_queries = [r for r in results if r['execution_time'] and r['execution_time'] > 10]
        
        print(f"   • Queries taking >5 seconds: {len(slow_queries)}")
        print(f"   • Queries taking >10 seconds: {len(very_slow_queries)}")
        
        if slow_queries:
            print(f"\n🔍 Slow Query Patterns:")
            for query in slow_queries:
                print(f"   • {query['description']}: {query['execution_time']:.2f}s "
                      f"(depth={query['max_depth']}, results={query['max_results']})")
        
        # Suggest new thresholds
        print(f"\n💡 Suggested Warning Thresholds (for pre-computed system):")
        
        # Find the minimum parameters that cause slowdowns
        slow_depths = [q['max_depth'] for q in slow_queries if q['execution_time']]
        slow_results = [q['max_results'] for q in slow_queries if q['execution_time']]
        
        if slow_depths and slow_results:
            min_slow_depth = min(slow_depths)
            min_slow_results = min(slow_results)
            
            print(f"   • Warn when depth >= {min_slow_depth} (was 5)")
            print(f"   • Warn when max_results >= {min_slow_results} (was 6)")
            print(f"   • Consider warning for combinations of depth >= {min_slow_depth-1} AND max_results >= {min_slow_results-1}")
        else:
            print(f"   • Current system performs well - consider raising thresholds:")
            print(f"   • Warn when depth >= 7 (was 5)")
            print(f"   • Warn when max_results >= 10 (was 6)")
        
        # Test multiple jobs
        print(f"\n🔄 Testing Multiple Job Performance:")
        multiple_job_cases = [
            ([test_job_id], "Single job"),
            ([test_job_id, 'R0001.1'], "Two jobs"),
            ([test_job_id, 'R0001.1', 'R0002.1'], "Three jobs"),
        ]
        
        for job_list, desc in multiple_job_cases:
            job_placeholders = ','.join(['?' for _ in job_list])
            multi_query = tree_query.replace('?', job_placeholders, 1)  # Replace first ? only
            
            params = job_list + [0.2, 5, 8, '', '', '', '', '', '', '', '']
            
            try:
                start_time = time.time()
                query_results = conn.execute(multi_query, params).fetchall()
                end_time = time.time()
                
                execution_time = end_time - start_time
                node_count = len(query_results)
                
                print(f"   • {desc}: {execution_time:.2f}s ({node_count} nodes)")
                
            except Exception as e:
                print(f"   • {desc}: ERROR - {str(e)[:50]}...")
        
        return results
        
    except Exception as e:
        print(f"❌ Error during performance testing: {e}")
        return None
    
    finally:
        conn.close()

def suggest_new_thresholds(results):
    """Analyze results and suggest new threshold values."""
    if not results:
        return
    
    print(f"\n🎯 Recommended New Threshold Configuration:")
    print("```javascript")
    print("// Updated thresholds for pre-computed career pathways")
    print("async function isExpensiveQuery(params) {")
    print("    const hasNoOrgFilters = !params.division && !params.business_unit && !params.location && !params.region;")
    print("    const isVeryDeepTree = params.depth >= 7;  // Raised from 5")
    print("    const isLowSimilarity = params.similarity <= 0.1;  // Lowered from 0.3")
    print("    const hasMultipleJobs = params.jobs.length > 2;  // Raised from 1")
    print("    const hasVeryHighMaxResults = params.max_results >= 10;  // Raised from 6")
    print("    ")
    print("    // Only warn for truly extreme combinations")
    print("    if (isVeryDeepTree && hasVeryHighMaxResults && hasNoOrgFilters) {")
    print("        return true;")
    print("    }")
    print("    ")
    print("    if (params.depth >= 8 && hasNoOrgFilters) {")
    print("        return true;")
    print("    }")
    print("    ")
    print("    if (hasVeryHighMaxResults && hasNoOrgFilters && isLowSimilarity && hasMultipleJobs) {")
    print("        return true;")
    print("    }")
    print("    ")
    print("    return false;")
    print("}")
    print("```")

if __name__ == '__main__':
    results = test_query_performance()
    if results:
        suggest_new_thresholds(results) 