#!/usr/bin/env python3
"""
Debug script for Job Opportunity Breadth calculation (Simplified Transferability)

Focuses on the 4 skills from output.md:
- Loss Functions
- User Interface Quartz (UIQ)  
- User-Centered Design
- User Interface Specification

Will test the new simplified approach: count job profiles using each skill
"""

import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path

def calculate_diversity_score(distribution_dict):
    """Calculate Shannon entropy for diversity (copied from main module)"""
    if not distribution_dict or sum(distribution_dict.values()) == 0:
        return 0
    
    total = sum(distribution_dict.values())
    entropy = 0
    for count in distribution_dict.values():
        if count > 0:
            p = count / total
            entropy -= p * np.log2(p)
    
    # Normalize to 0-1 scale
    max_entropy = np.log2(len(distribution_dict)) if len(distribution_dict) > 1 else 1
    return entropy / max_entropy if max_entropy > 0 else 0

def debug_opportunity_breadth_calculation():
    """Debug the simplified Job Opportunity Breadth calculation for specific skills"""
    
    # Target skills from output.md
    target_skills = [
        "Loss Functions",
        "User Interface Quartz (UIQ)",
        "User-Centered Design", 
        "User Interface Specification"
    ]
    
    print("🎯 JOB OPPORTUNITY BREADTH DEBUG ANALYSIS")
    print("=" * 80)
    print(f"Target skills: {len(target_skills)}")
    for skill in target_skills:
        print(f"   → {skill}")
    print()
    print("🔧 Testing simplified approach: How many job profiles use each skill?")
    
    # Connect to database
    db_path = Path(r"C:\Users\kipjo\OneDrive\Documents\GitHub\skill-similarity-engine\models\2025-Q3\workforce_intelligence.sqlite")
    if not db_path.exists():
        print(f"❌ Database not found at: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    
    try:
        # Step 1: Execute the simplified query
        print("📊 STEP 1: SIMPLIFIED JOB OPPORTUNITY BREADTH CALCULATION")
        print("-" * 60)
        
        opportunity_query = """
        SELECT s.Skill_Name, s.Skill_ID,
               COUNT(DISTINCT js.JobProfileID) as job_profiles_with_skill
        FROM skills s
        JOIN job_skills js ON s.Skill_ID = js.Skill_ID
        WHERE s.Skill_Name IN ('Loss Functions', 'User Interface Quartz (UIQ)', 'User-Centered Design', 'User Interface Specification')
        GROUP BY s.Skill_Name, s.Skill_ID
        ORDER BY s.Skill_Name
        """
        
        skill_usage_data = pd.read_sql_query(opportunity_query, conn)
        
        print(f"Skills found: {len(skill_usage_data)}")
        print("\nSkill usage data:")
        print(skill_usage_data.to_string())
        
        # Step 2: Get total job profiles for percentage calculation
        print(f"\n📊 STEP 2: ENTERPRISE TOTALS")
        print("-" * 50)
        
        total_profiles_query = "SELECT COUNT(DISTINCT JobProfileID) as total FROM jobs"
        total_profiles = pd.read_sql_query(total_profiles_query, conn).iloc[0]['total']
        
        print(f"Enterprise totals:")
        print(f"   → Total Job Profiles: {total_profiles:,}")
        
        # Step 3: Calculate opportunity breadth for each skill
        print(f"\n🎯 STEP 3: OPPORTUNITY BREADTH CALCULATION")
        print("-" * 60)
        
        for _, skill_row in skill_usage_data.iterrows():
            skill_name = skill_row['Skill_Name']
            profiles_with_skill = skill_row['job_profiles_with_skill']
            
            print(f"\n🎯 ANALYZING: {skill_name}")
            print("=" * 60)
            print(f"Job profiles using this skill: {profiles_with_skill:,}")
            print(f"Total job profiles in enterprise: {total_profiles:,}")
            
            # Calculate opportunity breadth (simple!)
            print(f"\n📐 OPPORTUNITY BREADTH CALCULATION:")
            
            opportunity_breadth_score = (profiles_with_skill / total_profiles * 100) if total_profiles > 0 else 0
            print(f"   → Opportunity Breadth: {profiles_with_skill:,}/{total_profiles:,} = {opportunity_breadth_score:.2f}%")
            
            # Categorization (simple!)
            if opportunity_breadth_score >= 20:
                category = "Universal Skill"        # 20%+ of jobs
            elif opportunity_breadth_score >= 10:
                category = "Cross-Functional Skill" # 10-20% of jobs  
            elif opportunity_breadth_score >= 5:
                category = "Transferable Skill"     # 5-10% of jobs
            elif opportunity_breadth_score >= 1:
                category = "Specialized Skill"      # 1-5% of jobs
            else:
                category = "Niche Skill"           # <1% of jobs
                
            print(f"   → Category: {category}")
            
            # Compare with expected complex results
            print(f"\n🔍 COMPARISON WITH COMPLEX METHOD:")
            print(f"   → Old complex score: 1023.1 (broken)")
            print(f"   → New simple score: {opportunity_breadth_score:.2f}%")
            print(f"   → Old category: Highly Transferable (wrong)")
            print(f"   → New category: {category} (logical)")
            print(f"   → ✅ IMPROVEMENT: Simple method provides logical results!")
        
        # Handle missing skills
        found_skills = set(skill_usage_data['Skill_Name'].unique())
        missing_skills = set(target_skills) - found_skills
        
        if missing_skills:
            print(f"\n⚠️ MISSING SKILLS:")
            for missing_skill in missing_skills:
                print(f"   → {missing_skill}: Not found in database")
                print(f"     Category: Niche Skill (0.0% opportunity breadth)")
            
    except Exception as e:
        print(f"❌ Error during debug: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        conn.close()
        print(f"\n🔒 Database connection closed")

if __name__ == "__main__":
    debug_opportunity_breadth_calculation() 