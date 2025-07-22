#!/usr/bin/env python3
"""
Debug script for transferability calculation issues

Focuses on the 4 skills from output.md:
- Loss Functions
- User Interface Quartz (UIQ)  
- User-Centered Design
- User Interface Specification

Will trace through every step of the calculation to find the 1023.1 mystery
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

def debug_transferability_calculation():
    """Debug the transferability calculation for specific skills"""
    
    # Target skills from output.md
    target_skills = [
        "Loss Functions",
        "User Interface Quartz (UIQ)",
        "User-Centered Design", 
        "User Interface Specification"
    ]
    
    print("🔍 TRANSFERABILITY DEBUG ANALYSIS")
    print("=" * 80)
    print(f"Target skills: {len(target_skills)}")
    for skill in target_skills:
        print(f"   → {skill}")
    print()
    
    # Connect to database
    db_path = Path(r"C:\Users\kipjo\OneDrive\Documents\GitHub\skill-similarity-engine\models\2025-Q3\workforce_intelligence.sqlite")
    if not db_path.exists():
        print(f"❌ Database not found at: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    
    try:
        # Step 1: Execute the original query and inspect raw data
        print("📊 STEP 1: RAW DATA EXTRACTION")
        print("-" * 50)
        
        transferability_query = """
        SELECT s.Skill_Name, s.Skill_ID,
               j.JobFunction, j.ManagementLevel, j.JobCategory,
               COUNT(DISTINCT js.JobProfileID) as profiles_in_context
        FROM skills s
        JOIN job_skills js ON s.Skill_ID = js.Skill_ID
        JOIN jobs j ON js.JobProfileID = j.JobProfileID
        WHERE s.Skill_Name IN ('Loss Functions', 'User Interface Quartz (UIQ)', 'User-Centered Design', 'User Interface Specification')
        GROUP BY s.Skill_Name, s.Skill_ID, j.JobFunction, j.ManagementLevel, j.JobCategory
        ORDER BY s.Skill_Name, j.JobFunction, j.ManagementLevel
        """
        
        transferability_data = pd.read_sql_query(transferability_query, conn)
        
        print(f"Raw data rows retrieved: {len(transferability_data)}")
        print("\nRaw data preview:")
        print(transferability_data.to_string())
        
        # Step 2: Calculate enterprise-wide totals
        print(f"\n📊 STEP 2: ENTERPRISE TOTALS")
        print("-" * 50)
        
        total_functions_query = "SELECT COUNT(DISTINCT JobFunction) as total FROM jobs"
        total_levels_query = "SELECT COUNT(DISTINCT ManagementLevel) as total FROM jobs"  
        total_categories_query = "SELECT COUNT(DISTINCT JobCategory) as total FROM jobs"
        
        total_functions = pd.read_sql_query(total_functions_query, conn).iloc[0]['total']
        total_levels = pd.read_sql_query(total_levels_query, conn).iloc[0]['total']
        total_categories = pd.read_sql_query(total_categories_query, conn).iloc[0]['total']
        
        print(f"Enterprise totals:")
        print(f"   → Total JobFunctions: {total_functions}")
        print(f"   → Total ManagementLevels: {total_levels}")
        print(f"   → Total JobCategories: {total_categories}")
        
        # Step 3: Process each skill individually
        print(f"\n🔍 STEP 3: SKILL-BY-SKILL ANALYSIS")
        print("-" * 50)
        
        for skill_name in target_skills:
            print(f"\n🎯 ANALYZING: {skill_name}")
            print("=" * 60)
            
            skill_contexts = transferability_data[transferability_data['Skill_Name'] == skill_name]
            
            if len(skill_contexts) == 0:
                print(f"   ❌ No data found for {skill_name}")
                continue
                
            print(f"Contexts found: {len(skill_contexts)}")
            print("Context details:")
            for _, context in skill_contexts.iterrows():
                print(f"   → Function: {context['JobFunction']}, Level: {context['ManagementLevel']}, Category: {context['JobCategory']}, Profiles: {context['profiles_in_context']}")
            
            # Calculate metrics step by step
            print(f"\n📐 METRIC CALCULATIONS:")
            
            # Domain breadth
            unique_functions = skill_contexts['JobFunction'].nunique()
            domain_breadth = unique_functions / total_functions if total_functions > 0 else 0
            print(f"   → Domain Breadth: {unique_functions}/{total_functions} = {domain_breadth:.4f}")
            
            # Level flexibility  
            unique_levels = skill_contexts['ManagementLevel'].nunique()
            level_flexibility = unique_levels / total_levels if total_levels > 0 else 0
            print(f"   → Level Flexibility: {unique_levels}/{total_levels} = {level_flexibility:.4f}")
            
            # Context adaptability
            unique_categories = skill_contexts['JobCategory'].nunique()
            context_adaptability = unique_categories / total_categories if total_categories > 0 else 0
            print(f"   → Context Adaptability: {unique_categories}/{total_categories} = {context_adaptability:.4f}")
            
            # Function entropy
            function_distribution = skill_contexts.groupby('JobFunction')['profiles_in_context'].sum()
            print(f"   → Function Distribution: {function_distribution.to_dict()}")
            function_entropy = calculate_diversity_score(function_distribution.to_dict())
            print(f"   → Function Entropy: {function_entropy:.4f}")
            
            # Overall transferability score calculation
            print(f"\n🧮 TRANSFERABILITY SCORE CALCULATION:")
            component_1 = domain_breadth * 40
            component_2 = level_flexibility * 30  
            component_3 = context_adaptability * 20
            component_4 = function_entropy * 10
            
            print(f"   → Domain component: {domain_breadth:.4f} × 40 = {component_1:.4f}")
            print(f"   → Level component: {level_flexibility:.4f} × 30 = {component_2:.4f}")
            print(f"   → Category component: {context_adaptability:.4f} × 20 = {component_3:.4f}")
            print(f"   → Entropy component: {function_entropy:.4f} × 10 = {component_4:.4f}")
            
            pre_scale_score = component_1 + component_2 + component_3 + component_4
            final_score = pre_scale_score * 100
            
            print(f"   → Pre-scale sum: {pre_scale_score:.4f}")
            print(f"   → Final score (×100): {final_score:.4f}")
            
            # Categorization
            if final_score >= 80:
                category = "Highly Transferable"
            elif final_score >= 60:
                category = "Moderately Transferable"
            elif final_score >= 40:
                category = "Somewhat Transferable"
            elif final_score >= 20:
                category = "Limited Transferability"
            else:
                category = "Context Specific"
                
            print(f"   → Category: {category}")
            
            # Compare with output.md values
            print(f"\n🔍 COMPARISON WITH OUTPUT.MD:")
            print(f"   → Expected transferability_score: 1023.1")
            print(f"   → Calculated transferability_score: {final_score:.1f}")
            print(f"   → Expected category: Highly Transferable")
            print(f"   → Calculated category: {category}")
            print(f"   → ⚠️ MATCH: {'✅' if abs(final_score - 1023.1) < 0.1 else '❌'}")
            
    except Exception as e:
        print(f"❌ Error during debug: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        conn.close()
        print(f"\n🔒 Database connection closed")

if __name__ == "__main__":
    debug_transferability_calculation() 