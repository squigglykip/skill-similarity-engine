#!/usr/bin/env python3
"""
Comprehensive debug script for career pathways chart
This will analyze the exact data and show us what the chart should look like
"""

import sqlite3
import json
import requests
from pprint import pprint

def test_database_direct():
    """Test the database directly to see raw data"""
    print("=" * 80)
    print("1. TESTING DATABASE DIRECTLY")
    print("=" * 80)
    
    db = sqlite3.connect('models/2025-Q2/business_context.sqlite')
    db.row_factory = sqlite3.Row
    
    # Test the exact query used by the API
    query = """
    SELECT cp.similarity_score, j.JobProfile as job_title, j.JobFamily as job_family
    FROM career_pathways cp
    JOIN jobs j ON cp.target_job_id = j.JobProfileID
    WHERE cp.source_job_id = ?
    ORDER BY cp.similarity_rank
    """
    
    job_id = 'R0276.5'
    pathways = db.execute(query, (job_id,)).fetchall()
    
    print(f"Found {len(pathways)} pathways for {job_id}:")
    print()
    
    scores = []
    for i, pathway in enumerate(pathways, 1):
        score = pathway['similarity_score']
        scores.append(score)
        print(f"  {i:2d}. {score:.3f} ({score*100:5.1f}%) - {pathway['job_title']}")
    
    print()
    print(f"Score Statistics:")
    print(f"  Min:     {min(scores):.3f} ({min(scores)*100:.1f}%)")
    print(f"  Max:     {max(scores):.3f} ({max(scores)*100:.1f}%)")
    print(f"  Average: {sum(scores)/len(scores):.3f} ({sum(scores)/len(scores)*100:.1f}%)")
    
    db.close()
    return pathways

def test_api_endpoint():
    """Test the API endpoint to see what it returns"""
    print("\n" + "=" * 80)
    print("2. TESTING API ENDPOINT")
    print("=" * 80)
    
    try:
        response = requests.get('http://localhost:5000/api/career-pathways-distribution/R0276.5')
        if response.status_code == 200:
            data = response.json()
            print(f"API returned {len(data)} pathways:")
            print()
            
            for i, pathway in enumerate(data, 1):
                score = pathway['similarity_score']
                print(f"  {i:2d}. {score:.3f} ({score*100:5.1f}%) - {pathway['job_title']}")
            
            return data
        else:
            print(f"API Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"API Connection Error: {e}")
        return None

def analyze_quintiles(pathways):
    """Analyze how pathways should be distributed in quintiles"""
    print("\n" + "=" * 80)
    print("3. QUINTILE ANALYSIS")
    print("=" * 80)
    
    if not pathways:
        print("No pathways data available")
        return
    
    # Convert to the format the JavaScript uses
    js_pathways = []
    for pathway in pathways:
        if isinstance(pathway, dict):
            # From API
            js_pathways.append({
                'similarity_score': pathway['similarity_score'],
                'job_title': pathway['job_title'],
                'job_family': pathway['job_family']
            })
        else:
            # From database
            js_pathways.append({
                'similarity_score': pathway['similarity_score'],
                'job_title': pathway['job_title'],
                'job_family': pathway['job_family']
            })
    
    # JavaScript quintile logic (exactly as in the HTML)
    quintiles = {
        '0-20%': 0,
        '20-40%': 0,
        '40-60%': 0,
        '60-80%': 0,
        '80-100%': 0
    }
    
    print("Pathway assignment to quintiles:")
    for i, pathway in enumerate(js_pathways, 1):
        score = pathway['similarity_score'] * 100
        
        # Use exact same logic as JavaScript
        if score < 20:
            quintile = '0-20%'
        elif score < 40:
            quintile = '20-40%'
        elif score < 60:
            quintile = '40-60%'
        elif score < 80:
            quintile = '60-80%'
        else:
            quintile = '80-100%'
        
        quintiles[quintile] += 1
        print(f"  {i:2d}. {score:5.1f}% -> {quintile:8s} - {pathway['job_title'][:50]}")
    
    print("\nQuintile Distribution:")
    max_count = max(quintiles.values()) if quintiles.values() else 1
    for quintile, count in quintiles.items():
        percentage = (count / len(js_pathways)) * 100 if js_pathways else 0
        bar = "█" * count + "░" * (max_count - count)
        print(f"  {quintile:8s}: {count:2d} jobs ({percentage:4.1f}%) {bar}")
    
    return quintiles

def analyze_chart_heights(quintiles):
    """Calculate what the chart bar heights should be"""
    print("\n" + "=" * 80)
    print("4. CHART HEIGHT CALCULATION")
    print("=" * 80)
    
    if not quintiles:
        print("No quintiles data available")
        return
    
    # JavaScript chart logic (exactly as in the HTML)
    max_count = max(list(quintiles.values()) + [1])  # Ensure minimum of 1
    max_height = 80  # Maximum height for bars in pixels
    
    print(f"Max count: {max_count}")
    print(f"Max height: {max_height}px")
    print()
    print("Chart bar heights:")
    
    for quintile, count in quintiles.items():
        height = max(3, (count / max_count) * max_height) if count > 0 else 3
        percentage = (height / max_height) * 100
        visual_bar = "█" * int(height / 5) if height >= 5 else "▌"
        print(f"  {quintile:8s}: {count:2d} jobs -> {height:5.1f}px ({percentage:4.1f}% of max) {visual_bar}")

def test_filtering_logic(pathways):
    """Test the filtering logic for different thresholds"""
    print("\n" + "=" * 80)
    print("5. FILTERING LOGIC TEST")
    print("=" * 80)
    
    if not pathways:
        print("No pathways data available")
        return
    
    thresholds = [0.9, 0.8, 0.7, 0.6, 0.5, 0.45, 0.4]
    
    print("Filtering test (JavaScript logic):")
    for threshold in thresholds:
        filtered = [p for p in pathways if p['similarity_score'] >= threshold]
        percentage = int(threshold * 100)
        print(f"  {percentage:3d}% threshold: {len(filtered):2d}/{len(pathways)} jobs pass")
        
        if len(filtered) <= 5:  # Show which jobs pass
            for job in filtered:
                score_pct = job['similarity_score'] * 100
                print(f"      {score_pct:5.1f}% - {job['job_title'][:40]}")

def debug_html_vs_expected():
    """Compare what HTML should show vs what it probably is showing"""
    print("\n" + "=" * 80)
    print("6. HTML DEBUG ANALYSIS")
    print("=" * 80)
    
    print("Based on the screenshot, the HTML is showing:")
    print("  - Horizontal bars instead of vertical bars")
    print("  - Wrong quintile distribution")
    print("  - 100% matches showing incorrectly")
    print()
    print("Expected based on API data:")
    print("  - 0-20%:   0 jobs (empty bar)")
    print("  - 20-40%:  0 jobs (empty bar)")
    print("  - 40-60%:  8 jobs (tall bar)")
    print("  - 60-80%:  0 jobs (empty bar)")
    print("  - 80-100%: 4 jobs (medium bar)")
    print()
    print("Likely HTML issues:")
    print("  1. CSS flexbox orientation wrong")
    print("  2. Bar height calculation not working")
    print("  3. Data not reaching the chart update function")
    print("  4. JavaScript quintile logic different from what we calculated")

def generate_test_data():
    """Generate test data for debugging"""
    print("\n" + "=" * 80)
    print("7. TEST DATA GENERATION")
    print("=" * 80)
    
    # This is the exact data from the API response
    test_pathways = [
        {"job_family": "Human Resources", "job_title": "Employee Relations Specialist - Manager", "similarity_score": 1.0},
        {"job_family": "Executive Leadership", "job_title": "Associate Business Unit Leader", "similarity_score": 1.0},
        {"job_family": "Banking Operations", "job_title": "Settlement Officer - Executive Director", "similarity_score": 1.0},
        {"job_family": "Banking Operations", "job_title": "Associate Operations Manager", "similarity_score": 1.0},
        {"job_family": "Human Resources", "job_title": "HR Analyst - Director", "similarity_score": 0.5},
        {"job_family": "Data & Analytics", "job_title": "Graduate - Business Intelligence Analyst", "similarity_score": 0.5},
        {"job_family": "Executive Leadership", "job_title": "Senior Associate Regional Head", "similarity_score": 0.5},
        {"job_family": "Banking Operations", "job_title": "Analyst - Operations Analyst", "similarity_score": 0.486},
        {"job_family": "Executive Leadership", "job_title": "Analyst - Regional Head", "similarity_score": 0.486},
        {"job_family": "Finance & Accounting", "job_title": "Budget Analyst - Executive Director", "similarity_score": 0.486},
        {"job_family": "Risk & Compliance", "job_title": "Regulatory Specialist - Director", "similarity_score": 0.486},
        {"job_family": "Human Resources", "job_title": "Employee Relations Specialist - Manager", "similarity_score": 0.486}
    ]
    
    print("JavaScript code to test in browser console:")
    print()
    print("// Copy this into browser console to test:")
    json_str = json.dumps(test_pathways, indent=2)
    print(f"const testPathways = {json_str};")
    print("""
// Test the quintile calculation
const quintiles = {
    '0-20%': 0,
    '20-40%': 0,
    '40-60%': 0,
    '60-80%': 0,
    '80-100%': 0
};

testPathways.forEach(pathway => {
    const score = pathway.similarity_score * 100;
    if (score < 20) quintiles['0-20%']++;
    else if (score < 40) quintiles['20-40%']++;
    else if (score < 60) quintiles['40-60%']++;
    else if (score < 80) quintiles['60-80%']++;
    else quintiles['80-100%']++;
});

console.log('Quintiles:', quintiles);

// Test chart height calculation
const maxCount = Math.max(...Object.values(quintiles), 1);
const maxHeight = 80;

Object.entries(quintiles).forEach(([quintile, count]) => {
    const height = count > 0 ? Math.max(3, (count / maxCount) * maxHeight) : 3;
    console.log(`${quintile}: ${count} jobs -> ${height}px`);
});
""")

def main():
    """Run all debug tests"""
    print("CAREER PATHWAYS CHART DEBUG ANALYSIS")
    print("=====================================")
    print("Testing R0276.5 (Data Scientist job)")
    
    # Test 1: Database direct
    db_pathways = test_database_direct()
    
    # Test 2: API endpoint
    api_pathways = test_api_endpoint()
    
    # Test 3: Use API data if available, otherwise database
    pathways_to_analyze = api_pathways if api_pathways else [dict(p) for p in db_pathways]
    
    # Test 4: Quintile analysis
    quintiles = analyze_quintiles(pathways_to_analyze)
    
    # Test 5: Chart heights
    if quintiles:
        analyze_chart_heights(quintiles)
    
    # Test 6: Filtering logic
    if pathways_to_analyze:
        test_filtering_logic(pathways_to_analyze)
    
    # Test 7: HTML debug
    debug_html_vs_expected()
    
    # Test 8: Generate test data
    generate_test_data()
    
    print("\n" + "=" * 80)
    print("DEBUG COMPLETE")
    print("=" * 80)
    print("Now you can:")
    print("1. Run this script to see what the data should show")
    print("2. Copy the JavaScript test code into browser console")
    print("3. Compare with what the HTML is actually showing")
    print("4. Fix the discrepancies in job_explorer.html")

if __name__ == "__main__":
    main() 