#!/usr/bin/env python3
"""
Skill Enrichment Analysis - Rarity Intelligence & Growth Trends

This script enriches a specific skill list with:
1. Enterprise rarity intelligence (from role typology analysis)
2. Temporal growth trends (skill demand changes over time)
3. Business-ready insights for talent development teams

Input: List of skills from business team
Output: Enriched CSV with actionable skill intelligence
"""

import pandas as pd
import numpy as np
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime, timedelta
import warnings
from typing import Dict, List, Tuple, Optional

warnings.filterwarnings('ignore')

# =============================================================================
# CONFIGURATION
# =============================================================================

DATABASE_FILE = "models/2025-Q3/workforce_intelligence.sqlite"

class SkillEnrichmentConfig:
    """Configuration for skill enrichment analysis"""
    
    # Database configuration
    DATABASE_PATH = DATABASE_FILE
    
    # Skill rarity thresholds (from role typology analysis)
    RARITY_THRESHOLDS = {
        'rare': 5.0,        # <5% = rare skill
        'uncommon': 20.0,   # 5-20% = uncommon skill  
        'common': 50.0,     # 20-50% = common skill
        # >50% = universal skill
    }
    
    # Temporal analysis configuration
    TEMPORAL_ANALYSIS = {
        'lookback_years': 5,        # Analyze last 5 years of trends
        'minimum_movements': 10,    # Minimum movements to calculate reliable trends
        'growth_significance': 0.1,  # 10% growth threshold for "growing demand"
        'recent_weight': 2.0        # Weight recent years 2x higher
    }
    
    # Output configuration
    OUTPUT_COLUMNS = [
        'skill_id',
        'skill_name', 
        'skill_category',
        'skill_type',
        'current_prevalence_percent',
        'rarity_category',
        'rarity_score',
        'total_job_profiles_using',
        'growth_trend_5yr',
        'growth_category',
        'recent_demand_score',
        'skill_mobility_score',
        'skill_mobility_tier',
        'skill_destinations',
        'skill_transitions',
        'strategic_priority',
        'development_recommendation'
    ]

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def connect_database():
    """Connect to the workforce intelligence database"""
    try:
        conn = sqlite3.connect(SkillEnrichmentConfig.DATABASE_PATH)
        print(f"✅ Connected to database: {SkillEnrichmentConfig.DATABASE_PATH}")
        return conn
    except sqlite3.OperationalError as e:
        raise FileNotFoundError(f"Could not connect to database: {e}")

def load_skill_universe(conn):
    """Load complete skill universe with current prevalence"""
    print("📚 Loading complete skill universe...")
    
    # Get total job profiles for prevalence calculation
    total_profiles_query = "SELECT COUNT(DISTINCT JobProfileID) as total FROM jobs"
    total_profiles = pd.read_sql_query(total_profiles_query, conn).iloc[0]['total']
    
    # Calculate current skill prevalence
    skill_prevalence_query = f"""
    SELECT 
        s.Skill_ID,
        s.Skill_Name,
        s.Category,
        s.SkillType,
        COUNT(DISTINCT js.JobProfileID) as profiles_using_skill,
        COUNT(DISTINCT js.JobProfileID) * 100.0 / {total_profiles} as prevalence_percentage,
        {total_profiles} - COUNT(DISTINCT js.JobProfileID) as rarity_score
    FROM skills s
    LEFT JOIN job_skills js ON s.Skill_ID = js.Skill_ID
    GROUP BY s.Skill_ID, s.Skill_Name, s.Category, s.SkillType
    ORDER BY prevalence_percentage ASC
    """
    
    skill_universe = pd.read_sql_query(skill_prevalence_query, conn)
    
    # Handle null values
    skill_universe['prevalence_percentage'].fillna(0.0, inplace=True)
    skill_universe['profiles_using_skill'].fillna(0, inplace=True)
    skill_universe['rarity_score'].fillna(total_profiles, inplace=True)
    
    # Categorize by rarity
    def categorize_rarity(prevalence):
        if prevalence < SkillEnrichmentConfig.RARITY_THRESHOLDS['rare']:
            return 'Rare'
        elif prevalence < SkillEnrichmentConfig.RARITY_THRESHOLDS['uncommon']:
            return 'Uncommon'
        elif prevalence < SkillEnrichmentConfig.RARITY_THRESHOLDS['common']:
            return 'Common'
        else:
            return 'Universal'
    
    skill_universe['rarity_category'] = skill_universe['prevalence_percentage'].apply(categorize_rarity)
    
    print(f"   → Loaded {len(skill_universe):,} skills from enterprise")
    print(f"   → Total job profiles: {total_profiles:,}")
    
    return skill_universe

def calculate_skill_growth_trends(conn, skill_universe):
    """Calculate temporal growth trends for skills based on movement data"""
    print("📈 Calculating skill growth trends from movement patterns...")
    
    try:
        # Get movement data with temporal information
        # First, let's check what columns are available in movement_fact
        movement_query = """
        SELECT 
            mf.movement_year,
            p_from.JobProfileID as JobProfileID_from,
            p_to.JobProfileID as JobProfileID_to,
            mf.movement_count
        FROM movement_fact mf
        JOIN positions p_from ON mf.from_position = p_from.[Position Number]
        JOIN positions p_to ON mf.to_position = p_to.[Position Number]
        WHERE mf.movement_year >= 2020
        AND p_from.JobProfileID IS NOT NULL 
        AND p_to.JobProfileID IS NOT NULL
        """
        
        movement_df = pd.read_sql_query(movement_query, conn)
        print(f"   → Loaded {len(movement_df):,} movement records with job profiles")
        
    except Exception as e:
        print(f"   ⚠️  Could not load movement data for temporal analysis: {str(e)}")
        print("   → Continuing with rarity analysis only (no growth trends)")
        return {}  # Return empty dict for trends
    
    # Get job-skill mappings
    job_skills_query = """
    SELECT JobProfileID, Skill_ID
    FROM job_skills
    """
    job_skills = pd.read_sql_query(job_skills_query, conn)
    
    # Calculate skill demand by year (skills in destination roles)
    skill_growth_data = []
    
    print("   → Analyzing skill demand trends by year...")
    
    for year in sorted(movement_df['movement_year'].unique()):
        year_movements = movement_df[movement_df['movement_year'] == year]
        
        # Get destination job profiles for this year
        destination_profiles = year_movements.groupby('JobProfileID_to')['movement_count'].sum().reset_index()
        destination_profiles.columns = ['JobProfileID', 'demand_weight']
        
        # Join with skills
        year_skill_demand = destination_profiles.merge(
            job_skills, 
            on='JobProfileID', 
            how='inner'
        )
        
        # Aggregate skill demand for this year
        year_skill_summary = year_skill_demand.groupby('Skill_ID')['demand_weight'].sum().reset_index()
        year_skill_summary['year'] = year
        
        skill_growth_data.append(year_skill_summary)
    
    # Combine all years
    if skill_growth_data:
        skill_growth_df = pd.concat(skill_growth_data, ignore_index=True)
        
        # Calculate growth trends
        skill_trends = {}
        
        for skill_id in skill_growth_df['Skill_ID'].unique():
            skill_yearly = skill_growth_df[skill_growth_df['Skill_ID'] == skill_id].sort_values('year')
            
            if len(skill_yearly) >= 3:  # Need at least 3 years for trend
                # Calculate compound annual growth rate (CAGR)
                first_year_demand = skill_yearly.iloc[0]['demand_weight']
                last_year_demand = skill_yearly.iloc[-1]['demand_weight']
                years = len(skill_yearly) - 1
                
                if first_year_demand > 0:
                    growth_rate = (last_year_demand / first_year_demand) ** (1/years) - 1
                else:
                    growth_rate = 0.0
                
                # Calculate recent demand score (weighted toward recent years)
                recent_demand = 0
                total_weight = 0
                for _, row in skill_yearly.iterrows():
                    year_weight = 1 + (row['year'] - skill_yearly.iloc[0]['year']) * 0.2  # Recent years weighted higher
                    recent_demand += row['demand_weight'] * year_weight
                    total_weight += year_weight
                
                recent_demand_score = recent_demand / total_weight if total_weight > 0 else 0
                
                skill_trends[skill_id] = {
                    'growth_trend_5yr': growth_rate,
                    'recent_demand_score': recent_demand_score,
                    'total_movements': skill_yearly['demand_weight'].sum()
                }
    
    else:
        skill_trends = {}
    
    print(f"   → Calculated growth trends for {len(skill_trends):,} skills")
    
    return skill_trends

def categorize_growth_trend(growth_rate):
    """Categorize growth trend into business-friendly labels"""
    if growth_rate > 0.2:  # >20% annual growth
        return "High Growth"
    elif growth_rate > 0.1:  # 10-20% annual growth  
        return "Growing"
    elif growth_rate > -0.05:  # -5% to 10% (stable)
        return "Stable"
    elif growth_rate > -0.15:  # -15% to -5% (declining)
        return "Declining"
    else:  # <-15% (steep decline)
        return "Steep Decline"

def calculate_strategic_priority(row):
    """Calculate strategic priority based on rarity and growth"""
    rarity_weight = {
        'Rare': 4,
        'Uncommon': 3,
        'Common': 2,
        'Universal': 1
    }
    
    growth_weight = {
        'High Growth': 4,
        'Growing': 3,
        'Stable': 2,
        'Declining': 1,
        'Steep Decline': 0
    }
    
    rarity_score = rarity_weight.get(row.get('rarity_category'), 1)
    growth_score = growth_weight.get(row.get('growth_category'), 1)
    
    # Combined priority score (1-8 scale)
    priority_score = (rarity_score + growth_score) / 2
    
    if priority_score >= 3.5:
        return "Critical"
    elif priority_score >= 2.5:
        return "High"
    elif priority_score >= 1.5:
        return "Medium"
    else:
        return "Low"

def generate_development_recommendation(row):
    """Generate actionable development recommendations"""
    rarity = row.get('rarity_category', '')
    growth = row.get('growth_category', '')
    priority = row.get('strategic_priority', '')
    mobility_tier = row.get('skill_mobility_tier', '')
    
    if priority == "Critical":
        if "Growth" in growth:
            return "Immediate focus: High-demand, rare skill with strong growth trajectory"
        else:
            return "Essential capability: Highly differentiated skill for competitive advantage"
    
    elif priority == "High":
        if rarity in ['Rare', 'Uncommon']:
            if 'Launchpad' in mobility_tier:
                return "Strategic investment: Rare skill that opens multiple career pathways"
            else:
                return "Specialist development: Build expertise in niche, valuable capability"
        else:
            return "Growth opportunity: Develop expanding skill area for career advancement"
    
    elif priority == "Medium":
        if 'Launchpad' in mobility_tier:
            return "Foundation builder: Skill that facilitates learning other capabilities"
        elif growth == "Stable":
            return "Foundation skill: Maintain competency in established capability"
        else:
            return "Monitor and assess: Track for future development priority"
    
    else:
        return "Lower priority: Consider for longer-term development planning"

def calculate_diversity_score(transition_counts):
    """
    Calculate Shannon diversity index for transition patterns.
    Higher score = more diverse transitions (higher mobility)
    Lower score = concentrated transitions (lower mobility)
    """
    if len(transition_counts) == 0:
        return 0.0
    
    # Convert to probabilities
    total = sum(transition_counts.values())
    if total == 0:
        return 0.0
    
    probabilities = [count / total for count in transition_counts.values()]
    
    # Calculate Shannon entropy
    entropy = -sum(p * np.log2(p) for p in probabilities if p > 0)
    
    # Normalize by maximum possible entropy for this number of categories
    max_entropy = np.log2(len(probabilities)) if len(probabilities) > 1 else 1
    
    return entropy / max_entropy if max_entropy > 0 else 0.0

def calculate_skill_mobility_score(skill_metrics):
    """Calculate 0-100 mobility score for skills"""
    
    # Component weights (same as job profiles)
    MOBILITY_SCORE_WEIGHTS = {
        'diversity_component': 40,      # Shannon diversity (0-40 points)
        'destination_component': 30,    # Unique destinations (0-30 points)
        'volume_component': 20,         # Movement volume (0-20 points) 
        'cross_boundary_component': 10  # Cross-boundary moves (0-10 points)
    }
    
    # Component 1: Diversity Score (0-40 points)
    diversity_component = skill_metrics['diversity_score'] * MOBILITY_SCORE_WEIGHTS['diversity_component']
    
    # Component 2: Destination Variety (0-30 points)
    # Scale: 10+ destinations = max points
    destination_component = min(
        skill_metrics['unique_destinations'] / 10 * MOBILITY_SCORE_WEIGHTS['destination_component'], 
        MOBILITY_SCORE_WEIGHTS['destination_component']
    )
    
    # Component 3: Movement Volume (0-20 points)  
    # Scale: 100+ movements = max points
    volume_component = min(
        skill_metrics['total_movements'] / 100 * MOBILITY_SCORE_WEIGHTS['volume_component'],
        MOBILITY_SCORE_WEIGHTS['volume_component']
    )
    
    # Component 4: Cross-Boundary Movements (0-10 points)
    cross_boundary_rate = skill_metrics.get('cross_category_rate', 0)
    cross_boundary_component = cross_boundary_rate * MOBILITY_SCORE_WEIGHTS['cross_boundary_component']
    
    # Total mobility score
    total_mobility_score = diversity_component + destination_component + volume_component + cross_boundary_component
    
    # Determine mobility tier
    mobility_tier = get_skill_mobility_tier(total_mobility_score)
    
    return {
        'mobility_score': round(total_mobility_score, 1),
        'mobility_tier': mobility_tier,
        'components': {
            'diversity': round(diversity_component, 1),
            'destinations': round(destination_component, 1),
            'volume': round(volume_component, 1),
            'cross_boundary': round(cross_boundary_component, 1)
        }
    }

def get_skill_mobility_tier(score):
    """Convert mobility score to descriptive tier for skills"""
    MOBILITY_TIERS = {
        (85, 100): "Super Launchpad Skill",
        (70, 84): "Strong Launchpad Skill", 
        (55, 69): "Moderate Launchpad Skill",
        (40, 54): "Standard Mobility Skill",
        (25, 39): "Limited Mobility Skill",
        (0, 24): "Skill Silo"
    }
    
    for (min_score, max_score), tier_name in MOBILITY_TIERS.items():
        if min_score <= score <= max_score:
            return tier_name
    return "Unknown"

def calculate_skill_mobility_for_list(conn, skill_list):
    """Calculate skill mobility scores for a specific list of skills"""
    print("🌉 Calculating skill mobility scores for requested skills...")
    
    try:
        # Get skill transition data
        skill_transition_query = """
        SELECT 
            mf.movement_year,
            p_from.JobProfileID as JobProfileID_from,
            p_to.JobProfileID as JobProfileID_to,
            mf.movement_count
        FROM movement_fact mf
        JOIN positions p_from ON mf.from_position = p_from.[Position Number]
        JOIN positions p_to ON mf.to_position = p_to.[Position Number]
        WHERE mf.movement_year >= 2020
        AND p_from.JobProfileID IS NOT NULL 
        AND p_to.JobProfileID IS NOT NULL
        """
        
        movement_df = pd.read_sql_query(skill_transition_query, conn)
        
        # Get job-skill mappings
        job_skills_query = """
        SELECT js.JobProfileID, js.Skill_ID, s.Skill_Name, s.Category
        FROM job_skills js
        JOIN skills s ON js.Skill_ID = s.Skill_ID
        """
        job_skills_df = pd.read_sql_query(job_skills_query, conn)
        
        # Get skills from movements
        from_skills = movement_df.merge(job_skills_df, left_on='JobProfileID_from', right_on='JobProfileID', how='inner')
        to_skills = movement_df.merge(job_skills_df, left_on='JobProfileID_to', right_on='JobProfileID', how='inner')
        
        # Analyze skill-to-skill transitions
        skill_transitions = from_skills.merge(
            to_skills, 
            on=['movement_year', 'JobProfileID_from', 'JobProfileID_to', 'movement_count'],
            suffixes=('_from', '_to')
        )
        
        # Calculate mobility for requested skills only
        skill_mobility_results = {}
        
        for skill_name in skill_list:
            # Find skill ID
            skill_match = job_skills_df[job_skills_df['Skill_Name'].str.lower() == skill_name.lower()]
            
            if not skill_match.empty:
                skill_id = skill_match.iloc[0]['Skill_ID']
                
                # Get transitions from this skill to other skills
                from_transitions = skill_transitions[skill_transitions['Skill_ID_from'] == skill_id]
                
                if len(from_transitions) > 3:  # Minimum transitions for analysis
                    # Calculate diversity of destination skills
                    destination_skills = from_transitions['Skill_ID_to'].value_counts()
                    diversity_score = calculate_diversity_score(destination_skills.to_dict())
                    
                    # Count unique destination skills
                    unique_destinations = len(destination_skills)
                    
                    # Calculate total transition volume
                    total_movements = from_transitions['movement_count'].sum()
                    
                    # Calculate cross-category transitions
                    cross_category_moves = from_transitions[
                        from_transitions['Category_from'] != from_transitions['Category_to']
                    ]['movement_count'].sum()
                    cross_category_rate = cross_category_moves / total_movements if total_movements > 0 else 0
                    
                    # Calculate skill mobility score
                    skill_metrics = {
                        'diversity_score': diversity_score,
                        'unique_destinations': unique_destinations,
                        'total_movements': total_movements,
                        'cross_category_rate': cross_category_rate
                    }
                    
                    mobility_analysis = calculate_skill_mobility_score(skill_metrics)
                    
                    skill_mobility_results[skill_name] = {
                        'mobility_score': mobility_analysis['mobility_score'],
                        'mobility_tier': mobility_analysis['mobility_tier'],
                        'unique_destinations': unique_destinations,
                        'total_transitions': total_movements,
                        'diversity_score': diversity_score,
                        'cross_category_rate': cross_category_rate
                    }
                else:
                    # Insufficient data for mobility analysis
                    skill_mobility_results[skill_name] = {
                        'mobility_score': 0.0,
                        'mobility_tier': "Insufficient Data",
                        'unique_destinations': 0,
                        'total_transitions': 0,
                        'diversity_score': 0.0,
                        'cross_category_rate': 0.0
                    }
        
        print(f"   → Calculated mobility scores for {len(skill_mobility_results)} skills")
        return skill_mobility_results
        
    except Exception as e:
        print(f"   ⚠️  Skill mobility analysis failed: {str(e)}")
        return {}

# =============================================================================
# MAIN ENRICHMENT FUNCTION
# =============================================================================

def enrich_skill_list(skill_list: List[str], output_filename: Optional[str] = None):
    """
    Enrich a list of skills with rarity intelligence and growth trends
    
    Args:
        skill_list: List of skill names to analyze
        output_filename: Optional CSV filename for output
    
    Returns:
        DataFrame with enriched skill analysis
    """
    
    print("🎯 SKILL ENRICHMENT ANALYSIS")
    print("="*60)
    print(f"📝 Analyzing {len(skill_list)} skills from business team")
    
    # Connect to database
    conn = connect_database()
    
    try:
        # Load skill universe with rarity intelligence
        skill_universe = load_skill_universe(conn)
        
        # Calculate growth trends
        skill_trends = calculate_skill_growth_trends(conn, skill_universe)
        
        # Calculate skill mobility scores
        skill_mobility_data = calculate_skill_mobility_for_list(conn, skill_list)
        
        # Filter to requested skills
        enriched_skills = []
        
        print(f"\n🔍 ENRICHING REQUESTED SKILLS:")
        print("-" * 40)
        
        for skill_name in skill_list:
            # Find matching skills (exact match first, then fuzzy)
            exact_match = skill_universe[skill_universe['Skill_Name'].str.lower() == skill_name.lower()]
            
            if not exact_match.empty:
                skill_row = exact_match.iloc[0].to_dict()
                skill_id = skill_row['Skill_ID']
                
                # Add growth trend data (with fallback if trends not available)
                if skill_trends:  # Check if trends were successfully calculated
                    trend_data = skill_trends.get(skill_id, {
                        'growth_trend_5yr': 0.0,
                        'recent_demand_score': 0.0,
                        'total_movements': 0
                    })
                else:
                    # Fallback when temporal analysis fails
                    trend_data = {
                        'growth_trend_5yr': 0.0,
                        'recent_demand_score': 0.0,
                        'total_movements': 0
                    }
                
                # Get skill mobility data
                mobility_data = skill_mobility_data.get(skill_name, {
                    'mobility_score': 0.0,
                    'mobility_tier': "Data Unavailable",
                    'unique_destinations': 0,
                    'total_transitions': 0
                })
                
                # Create enriched record
                enriched_record = {
                    'skill_id': skill_id,
                    'skill_name': skill_row['Skill_Name'],
                    'skill_category': skill_row.get('Category', 'Unknown'),
                    'skill_type': skill_row.get('SkillType', 'Unknown'),
                    'current_prevalence_percent': round(skill_row['prevalence_percentage'], 2),
                    'rarity_category': skill_row['rarity_category'],
                    'rarity_score': int(skill_row['rarity_score']),
                    'total_job_profiles_using': int(skill_row['profiles_using_skill']),
                    'growth_trend_5yr': round(trend_data['growth_trend_5yr'] * 100, 1),  # Convert to percentage
                    'growth_category': categorize_growth_trend(trend_data['growth_trend_5yr']) if skill_trends else "Data Unavailable",
                    'recent_demand_score': round(trend_data['recent_demand_score'], 1),
                    'skill_mobility_score': round(mobility_data['mobility_score'], 1),
                    'skill_mobility_tier': mobility_data['mobility_tier'],
                    'skill_destinations': mobility_data['unique_destinations'],
                    'skill_transitions': mobility_data['total_transitions'],
                    'strategic_priority': '',  # Will calculate after
                    'development_recommendation': ''  # Will calculate after
                }
                
                # Calculate strategic priority and recommendations
                enriched_record['strategic_priority'] = calculate_strategic_priority(enriched_record)
                enriched_record['development_recommendation'] = generate_development_recommendation(enriched_record)
                
                enriched_skills.append(enriched_record)
                
                print(f"✅ {skill_name}: {enriched_record['rarity_category']} skill, {enriched_record['growth_category']} trend")
                
            else:
                # Try fuzzy matching
                fuzzy_matches = skill_universe[skill_universe['Skill_Name'].str.contains(skill_name, case=False, na=False)]
                
                if not fuzzy_matches.empty:
                    print(f"🔍 '{skill_name}' - Found similar: {list(fuzzy_matches['Skill_Name'].head(3))}")
                else:
                    print(f"❌ '{skill_name}' - Not found in skill database")
        
        # Create results DataFrame
        if enriched_skills:
            results_df = pd.DataFrame(enriched_skills)
            
            # Sort by strategic priority and growth
            priority_order = {'Critical': 4, 'High': 3, 'Medium': 2, 'Low': 1}
            results_df['priority_rank'] = results_df['strategic_priority'].map(priority_order)
            results_df = results_df.sort_values(['priority_rank', 'growth_trend_5yr'], ascending=[False, False])
            results_df = results_df.drop('priority_rank', axis=1)
            
            # Output results
            print(f"\n📊 ENRICHMENT SUMMARY:")
            print("-" * 40)
            print(f"✅ Successfully enriched: {len(results_df)} skills")
            
            # Summary statistics
            rarity_dist = results_df['rarity_category'].value_counts()
            growth_dist = results_df['growth_category'].value_counts()
            mobility_dist = results_df['skill_mobility_tier'].value_counts()
            priority_dist = results_df['strategic_priority'].value_counts()
            
            print(f"\n📈 RARITY DISTRIBUTION:")
            for category, count in rarity_dist.items():
                print(f"   {category}: {count} skills")
                
            print(f"\n📈 GROWTH DISTRIBUTION:")
            for category, count in growth_dist.items():
                print(f"   {category}: {count} skills")
                
            print(f"\n🌉 SKILL MOBILITY DISTRIBUTION:")
            for category, count in mobility_dist.items():
                print(f"   {category}: {count} skills")
                
            print(f"\n🎯 STRATEGIC PRIORITY:")
            for priority, count in priority_dist.items():
                print(f"   {priority}: {count} skills")
            
            # Save to CSV
            if output_filename:
                output_path = Path(output_filename)
                results_df.to_csv(output_path, index=False)
                print(f"\n💾 Results saved to: {output_path}")
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = Path(f"skill_enrichment_analysis_{timestamp}.csv")
                results_df.to_csv(output_path, index=False)
                print(f"\n💾 Results saved to: {output_path}")
            
            return results_df
            
        else:
            print("❌ No skills could be enriched from the provided list")
            return pd.DataFrame()
            
    finally:
        conn.close()
        print("🔒 Database connection closed")

# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    
    # Example skill list (replace with your coworker's skills)
    example_skills = [
        "Python Programming",
        "Data Analysis", 
        "Machine Learning",
        "Risk Management",
        "Digital Marketing",
        "Customer Experience",
        "Project Management",
        "Artificial Intelligence",
        "Cloud Computing",
        "Agile Methodology"
    ]
    
    print("🚀 EXAMPLE SKILL ENRICHMENT ANALYSIS")
    print("="*60)
    print("This example shows how to enrich skills with rarity intelligence and growth trends.")
    print("Replace 'example_skills' with your coworker's actual skill list.")
    print()
    
    # Run enrichment analysis
    results = enrich_skill_list(example_skills, "example_skill_enrichment.csv")
    
    if not results.empty:
        print(f"\n🎯 TOP STRATEGIC PRIORITIES:")
        top_skills = results.head(5)
        for _, skill in top_skills.iterrows():
            print(f"   • {skill['skill_name']}: {skill['strategic_priority']} priority")
            print(f"     Rarity: {skill['rarity_category']} | Growth: {skill['growth_category']} | Mobility: {skill['skill_mobility_tier']}")
            print(f"     Prevalence: {skill['current_prevalence_percent']}% | Leads to {skill['skill_destinations']} other skills")
        
        # Show skill launchpads and silos
        launchpad_skills = results[results['skill_mobility_tier'].str.contains('Launchpad', na=False)]
        silo_skills = results[results['skill_mobility_tier'].str.contains('Silo', na=False)]
        
        if not launchpad_skills.empty:
            print(f"\n🌉 SKILL LAUNCHPADS (Bridge Skills):")
            for _, skill in launchpad_skills.iterrows():
                print(f"   • {skill['skill_name']}: Opens pathways to {skill['skill_destinations']} other skills")
        
        if not silo_skills.empty:
            print(f"\n🔒 SKILL SILOS (Specialised Skills):")
            for _, skill in silo_skills.iterrows():
                print(f"   • {skill['skill_name']}: Limited connections ({skill['skill_destinations']} destinations)") 