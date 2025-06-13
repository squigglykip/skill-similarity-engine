#!/usr/bin/env python3
"""
Test Script for Organised SQL Query Structure
============================================

Test the new organised SQL query system to ensure:
1. All query files load correctly
2. Query parsing works as expected
3. Database connectivity with real queries
4. Query categories and organisation function properly
"""

import sqlite3
import sys
from pathlib import Path

# Add the webapp directory to Python path
webapp_dir = Path(__file__).parent
sys.path.insert(0, str(webapp_dir))

def test_query_loader():
    """Test the SQL query loader system."""
    print("🔍 Testing SQL Query Loader...")
    
    try:
        from sql import queries
        print("✅ Successfully imported query loader")
        
        # Test listing categories
        categories = queries.list_categories()
        print(f"📁 Found {len(categories)} categories: {categories}")
        
        # Test each category
        for category in categories:
            query_list = queries.list_queries_in_category(category)
            print(f"   📄 {category}: {len(query_list)} queries")
            
            # Test getting a query from each category
            if query_list:
                first_query = query_list[0]
                query_sql = queries.get(category, first_query)
                if query_sql:
                    print(f"      ✅ Successfully loaded '{first_query}'")
                else:
                    print(f"      ❌ Failed to load '{first_query}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Query loader test failed: {e}")
        return False

def test_database_connectivity():
    """Test database connectivity with organised queries."""
    print("\n🗄️  Testing Database Connectivity...")
    
    # Database path
    db_path = Path(__file__).parent.parent.parent.parent / 'models' / '2025-Q2' / 'business_context.sqlite'
    
    if not db_path.exists():
        print(f"❌ Database not found at: {db_path}")
        return False
    
    print(f"✅ Database found: {db_path}")
    
    try:
        from sql import queries
        
        # Connect to database
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        
        # Test metadata queries
        print("📊 Testing metadata queries...")
        stats_query = queries.get('metadata', 'get_database_stats')
        if stats_query:
            stats = conn.execute(stats_query).fetchall()
            print(f"   ✅ Database stats: {len(stats)} metrics")
            for stat in stats[:3]:  # Show first 3 stats
                print(f"      {stat['metric']}: {stat['value']}")
        
        # Test job family query
        print("👥 Testing job family queries...")
        families_query = queries.get('jobs', 'get_job_families')
        if families_query:
            families = conn.execute(families_query).fetchall()
            print(f"   ✅ Job families found: {len(families)}")
            for family in families[:3]:  # Show first 3 families
                print(f"      {family['job_family']}: {family['job_count']} jobs")
        
        # Test D3 visualization query
        print("🌳 Testing D3 visualization queries...")
        tree_query = queries.get('d3_visualization', 'get_tree_data_for_family')
        if tree_query:
            # Test with a real family name
            if families:
                test_family = families[0]['job_family']
                tree_data = conn.execute(tree_query, (test_family, test_family, test_family)).fetchall()
                print(f"   ✅ Tree data for '{test_family}': {len(tree_data)} nodes")
        
        # Test skills queries
        print("🎯 Testing skills queries...")
        skills_query = queries.get('skills', 'get_skills_by_category')
        if skills_query:
            skills = conn.execute(skills_query).fetchall()
            print(f"   ✅ Skills by category: {len(skills)} categories")
            for skill_cat in skills[:3]:  # Show first 3 categories
                print(f"      {skill_cat['skill_category']}: {skill_cat['skill_count']} skills")
        
        # Test similarity queries
        print("🔗 Testing similarity queries...")
        similarity_query = queries.get('similarities', 'get_similarity_distribution')
        if similarity_query:
            similarities = conn.execute(similarity_query).fetchall()
            print(f"   ✅ Similarity distribution: {len(similarities)} categories")
            for sim in similarities:
                print(f"      {sim['similarity_category']}: {sim['count']} relationships (avg: {sim['avg_score']:.3f})")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database connectivity test failed: {e}")
        return False

def test_query_search():
    """Test query search functionality."""
    print("\n🔍 Testing Query Search...")
    
    try:
        from sql import queries
        
        # Search for specific terms
        search_terms = ['similarity', 'career', 'skills', 'd3', 'tree']
        
        for term in search_terms:
            results = queries.search_queries(term)
            total_found = sum(len(query_list) for query_list in results.values())
            print(f"   🔍 '{term}': found {total_found} queries across {len(results)} categories")
            
            # Show detailed results for first term
            if term == search_terms[0] and results:
                for category, query_names in results.items():
                    print(f"      📁 {category}: {', '.join(query_names[:2])}{'...' if len(query_names) > 2 else ''}")
        
        return True
        
    except Exception as e:
        print(f"❌ Query search test failed: {e}")
        return False

def test_query_info():
    """Test query information extraction."""
    print("\n📋 Testing Query Information...")
    
    try:
        from sql import queries
        
        # Test info for a few representative queries
        test_queries = [
            ('jobs', 'get_job_families'),
            ('similarities', 'get_similar_jobs'),
            ('d3_visualization', 'get_tree_data_for_family'),
            ('career_pathways', 'get_skills_gap_analysis')
        ]
        
        for category, query_name in test_queries:
            info = queries.get_query_info(category, query_name)
            if info:
                print(f"   📋 {category}.{query_name}:")
                print(f"      Parameters: {info['parameter_count']}")
                print(f"      Tables: {', '.join(info['tables_used'][:3])}{'...' if len(info['tables_used']) > 3 else ''}")
                print(f"      Lines: {info['line_count']}")
            else:
                print(f"   ❌ Failed to get info for {category}.{query_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Query info test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Organised SQL Query Structure")
    print("=" * 50)
    
    tests = [
        test_query_loader,
        test_database_connectivity,
        test_query_search,
        test_query_info
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        else:
            print()
    
    print("\n" + "=" * 50)
    print(f"🏁 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! SQL organisation is working correctly.")
        print("\n💡 Next steps:")
        print("   1. Update Flask app to use new SQL structure")
        print("   2. Test D3.js tree visualization with real data")
        print("   3. Deploy and validate in production environment")
    else:
        print("⚠️  Some tests failed. Please review the issues above.")
        
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 