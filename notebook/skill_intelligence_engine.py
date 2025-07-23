#!/usr/bin/env python3
"""
COMPLETE SKILLS INTELLIGENCE ENGINE - All-in-One
================================================================

This script combines the Skills Intelligence Engine with comprehensive testing
into a single file for easier exploration and experimentation.

Features:
- 4 Advanced Intelligence Modules (Temporal, Network, Supply/Demand, Transferability)
- Composite scoring system (0-100 scale with tier classifications)
- Comprehensive testing suite based on movement_analysis_engine.py patterns
- Memory monitoring and performance optimization
- Production-ready dual-engine integration compatibility

Usage:
    python skills_intelligence_complete.py

The script will automatically run comprehensive tests and analysis.
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
import math
import psutil

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

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_memory_usage():
    """Get current memory usage information (from movement_analysis_engine.py)"""
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024

def print_memory_status():
    """Print current memory usage (from movement_analysis_engine.py)"""
    memory_mb = get_memory_usage()
    print(f"💾 Memory Usage: {memory_mb:.1f} MB")

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
        movement_query = """
        WITH unique_positions AS (
            SELECT DISTINCT [Position Number], JobProfileID
            FROM positions
            WHERE JobProfileID IS NOT NULL
        )
        SELECT 
            mf.movement_year,
            p_from.JobProfileID as JobProfileID_from,
            p_to.JobProfileID as JobProfileID_to,
            mf.movement_count
        FROM movement_fact mf
        JOIN unique_positions p_from ON mf.from_position = p_from.[Position Number]
        JOIN unique_positions p_to ON mf.to_position = p_to.[Position Number]
        WHERE mf.movement_year >= 2020
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

# =============================================================================
# ADVANCED SKILLS INTELLIGENCE MODULES
# =============================================================================

# A. TEMPORAL SKILLS INTELLIGENCE
# =============================================================================

def calculate_skills_velocity_analysis(conn, lookback_years=5):
    """
    Calculate skills velocity - which skills are accelerating/decelerating in demand
    
    Returns:
        Dict with skill velocity metrics including momentum, acceleration, and trend stability
    """
    print("⏱️ Calculating Skills Velocity Analysis...")
    
    try:
        # Get movement data with temporal granularity
        velocity_query = f"""
        WITH unique_positions AS (
            SELECT DISTINCT [Position Number], JobProfileID
            FROM positions
            WHERE JobProfileID IS NOT NULL
        )
        SELECT 
            mf.movement_year,
            mf.movement_month,
            p_to.JobProfileID as destination_job,
            mf.movement_count
        FROM movement_fact mf
        JOIN unique_positions p_to ON mf.to_position = p_to.[Position Number]
        WHERE mf.movement_year >= {2024 - lookback_years}
        ORDER BY mf.movement_year, mf.movement_month
        """
        
        movement_temporal = pd.read_sql_query(velocity_query, conn)
        
        # Get job-skills mapping
        job_skills_query = """
        SELECT js.JobProfileID, js.Skill_ID, s.Skill_Name
        FROM job_skills js
        JOIN skills s ON js.Skill_ID = s.Skill_ID
        """
        job_skills = pd.read_sql_query(job_skills_query, conn)
        
        # Calculate monthly skill demand
        skill_temporal_demand = movement_temporal.merge(
            job_skills, 
            left_on='destination_job', 
            right_on='JobProfileID',
            how='inner'
        )
        
        # Aggregate by skill and time period
        skill_monthly_demand = skill_temporal_demand.groupby([
            'Skill_Name', 'movement_year', 'movement_month'
        ])['movement_count'].sum().reset_index()
        
        # Calculate velocity metrics for each skill
        skill_velocity_results = {}
        
        for skill_name in skill_monthly_demand['Skill_Name'].unique():
            skill_data = skill_monthly_demand[
                skill_monthly_demand['Skill_Name'] == skill_name
            ].sort_values(['movement_year', 'movement_month'])
            
            if len(skill_data) >= 12:  # Need at least 1 year of data
                # Fix: Properly parse movement_month string to extract month number
                skill_data = skill_data.copy()  # Avoid SettingWithCopyWarning
                skill_data['movement_month_num'] = pd.to_datetime(skill_data['movement_month']).dt.month
                
                # Create time series with proper numeric values
                skill_data['time_period'] = (
                    skill_data['movement_year'] * 12 + skill_data['movement_month_num']
                )
                
                # Calculate velocity (rate of change)
                skill_data['velocity'] = skill_data['movement_count'].diff()
                
                # Calculate acceleration (rate of change of velocity)
                skill_data['acceleration'] = skill_data['velocity'].diff()
                
                # Calculate momentum (recent trend strength)
                recent_periods = skill_data.tail(6)  # Last 6 months
                momentum = recent_periods['velocity'].mean()
                
                # Calculate trend stability (consistency of direction)
                velocity_changes = skill_data['velocity'].dropna()
                if len(velocity_changes) > 0:
                    positive_changes = (velocity_changes > 0).sum()
                    trend_stability = positive_changes / len(velocity_changes)
                else:
                    trend_stability = 0.5
                
                # Calculate overall growth rate
                first_value = skill_data['movement_count'].iloc[0]
                last_value = skill_data['movement_count'].iloc[-1]
                periods = len(skill_data)
                
                if first_value > 0:
                    growth_rate = (last_value / first_value) ** (1/periods) - 1
                else:
                    growth_rate = 0.0
                
                skill_velocity_results[skill_name] = {
                    'momentum': momentum,
                    'acceleration': skill_data['acceleration'].mean(),
                    'trend_stability': trend_stability,
                    'growth_rate': growth_rate,
                    'current_demand': last_value,
                    'peak_demand': skill_data['movement_count'].max(),
                    'demand_volatility': skill_data['movement_count'].std()
                }
        
        print(f"   → Calculated velocity for {len(skill_velocity_results):,} skills")
        return skill_velocity_results
        
    except Exception as e:
        print(f"   ⚠️ Skills velocity analysis failed: {str(e)}")
        return {}

def categorize_skill_velocity(velocity_data):
    """Categorize skill velocity into business-friendly labels"""
    momentum = velocity_data.get('momentum', 0)
    trend_stability = velocity_data.get('trend_stability', 0.5)
    growth_rate = velocity_data.get('growth_rate', 0)
    
    # High momentum + stable trend = accelerating
    if momentum > 5 and trend_stability > 0.7:
        return "Accelerating Demand"
    elif momentum > 2 and growth_rate > 0.1:
        return "Growing Momentum"
    elif abs(momentum) <= 2 and trend_stability > 0.6:
        return "Stable Demand"
    elif momentum < -2 and trend_stability < 0.4:
        return "Declining Momentum"
    elif momentum < -5:
        return "Steep Decline"
    else:
        return "Volatile Demand"

# B. SKILLS NETWORK ANALYSIS
# =============================================================================

def calculate_skills_network_analysis(conn):
    """
    Analyse skill co-occurrence networks and identify bridge skills
    
    Returns:
        Dict with network metrics including clustering, centrality, and bridge identification
    """
    print("🕸️ Calculating Skills Network Analysis...")
    
    try:
        # Get job-skills co-occurrence data
        job_skills_query = """
        SELECT js1.Skill_ID as skill_1, js2.Skill_ID as skill_2, 
               s1.Skill_Name as skill_1_name, s2.Skill_Name as skill_2_name,
               COUNT(DISTINCT js1.JobProfileID) as co_occurrence_count
        FROM job_skills js1
        JOIN job_skills js2 ON js1.JobProfileID = js2.JobProfileID
        JOIN skills s1 ON js1.Skill_ID = s1.Skill_ID
        JOIN skills s2 ON js2.Skill_ID = s2.Skill_ID
        WHERE js1.Skill_ID != js2.Skill_ID
        GROUP BY js1.Skill_ID, js2.Skill_ID, s1.Skill_Name, s2.Skill_Name
        HAVING COUNT(DISTINCT js1.JobProfileID) >= 3
        """
        
        skill_cooccurrence = pd.read_sql_query(job_skills_query, conn)
        
        # Calculate network metrics for each skill
        skill_network_results = {}
        
        # Get all unique skills in the network
        all_skills = set(skill_cooccurrence['skill_1_name'].unique()) | set(skill_cooccurrence['skill_2_name'].unique())
        
        for skill_name in all_skills:
            # Get all skills this skill connects to
            connections = skill_cooccurrence[
                (skill_cooccurrence['skill_1_name'] == skill_name) |
                (skill_cooccurrence['skill_2_name'] == skill_name)
            ]
            
            if len(connections) > 0:
                # Calculate degree centrality (number of connections)
                degree_centrality = len(connections)
                
                # Calculate weighted centrality (sum of co-occurrence strengths)
                weighted_centrality = connections['co_occurrence_count'].sum()
                
                # Calculate diversity of connections (Shannon entropy)
                connection_strengths = connections['co_occurrence_count'].values
                if len(connection_strengths) > 1:
                    probabilities = connection_strengths / connection_strengths.sum()
                    diversity_entropy = -sum(p * np.log2(p) for p in probabilities if p > 0)
                    max_entropy = np.log2(len(probabilities))
                    network_diversity = diversity_entropy / max_entropy if max_entropy > 0 else 0
            else:
                    network_diversity = 0
                
                # Calculate clustering coefficient (how connected are this skill's neighbors)
                # Simplified version: ratio of strong connections to total connections
                strong_connections = (connections['co_occurrence_count'] > connections['co_occurrence_count'].median()).sum()
                clustering_coefficient = strong_connections / len(connections) if len(connections) > 0 else 0
                
                # Identify skill categories this skill bridges
                skill_categories = set()
                for _, row in connections.iterrows():
                    # Get categories of connected skills (would need category mapping)
                    skill_categories.add("category")  # Placeholder - would map to actual categories
                
                skill_network_results[skill_name] = {
                    'degree_centrality': degree_centrality,
                    'weighted_centrality': weighted_centrality,
                    'network_diversity': network_diversity,
                    'clustering_coefficient': clustering_coefficient,
                    'total_cooccurrence_strength': weighted_centrality,
                    'average_connection_strength': weighted_centrality / degree_centrality if degree_centrality > 0 else 0,
                    'bridge_categories': len(skill_categories)
                }
        
        print(f"   → Calculated network metrics for {len(skill_network_results):,} skills")
        return skill_network_results
        
    except Exception as e:
        print(f"   ⚠️ Skills network analysis failed: {str(e)}")
        return {}

# C. SKILLS SUPPLY/DEMAND INTELLIGENCE
# =============================================================================

def calculate_skills_supply_demand_analysis(conn):
    """
    Calculate supply/demand dynamics for skills within the organisation
    
    Returns:
        Dict with supply/demand metrics including scarcity, competition, and market dynamics
    """
    print("⚖️ Calculating Skills Supply/Demand Analysis...")
    
    try:
        # Get current skill supply (people who have the skill)
        supply_query = """
        SELECT s.Skill_Name, s.Skill_ID,
               COUNT(DISTINCT js.JobProfileID) as roles_requiring_skill,
               COUNT(DISTINCT p.[Position Number]) as people_with_skill
        FROM skills s
        JOIN job_skills js ON s.Skill_ID = js.Skill_ID
        JOIN positions p ON js.JobProfileID = p.JobProfileID
        WHERE p.[Position Number] IS NOT NULL
        GROUP BY s.Skill_Name, s.Skill_ID
        """
        
        supply_data = pd.read_sql_query(supply_query, conn)
        
        # Get skill demand from movement patterns (destination roles)
        demand_query = """
        WITH unique_positions AS (
            SELECT DISTINCT [Position Number], JobProfileID
            FROM positions
            WHERE JobProfileID IS NOT NULL
        )
        SELECT s.Skill_Name,
               COUNT(DISTINCT mf.to_position) as destination_positions,
               SUM(mf.movement_count) as total_demand_movements
        FROM movement_fact mf
        JOIN unique_positions p ON mf.to_position = p.[Position Number]
        JOIN job_skills js ON p.JobProfileID = js.JobProfileID
        JOIN skills s ON js.Skill_ID = s.Skill_ID
        WHERE mf.movement_year >= 2022
        GROUP BY s.Skill_Name
        """
        
        demand_data = pd.read_sql_query(demand_query, conn)
        
        # Merge supply and demand data
        supply_demand = supply_data.merge(demand_data, on='Skill_Name', how='outer').fillna(0)
        
        skill_supply_demand_results = {}
        
        for _, row in supply_demand.iterrows():
            skill_name = row['Skill_Name']
            people_with_skill = row['people_with_skill']
            roles_requiring = row['roles_requiring_skill']
            demand_movements = row['total_demand_movements']
            
            # Calculate key metrics
            if people_with_skill > 0 and demand_movements > 0:
                # Scarcity index: demand relative to supply
                scarcity_index = demand_movements / people_with_skill
                
                # Competition index: people competing for roles requiring this skill
                competition_index = people_with_skill / roles_requiring if roles_requiring > 0 else 0
                
                # Market concentration: how concentrated is this skill
                total_people = supply_data['people_with_skill'].sum()
                market_concentration = people_with_skill / total_people if total_people > 0 else 0
                
                # Supply adequacy: can current supply meet demand?
                supply_adequacy = people_with_skill / demand_movements if demand_movements > 0 else 1
                
                skill_supply_demand_results[skill_name] = {
                    'internal_supply': int(people_with_skill),
                    'internal_demand': int(demand_movements),
                    'roles_requiring': int(roles_requiring),
                    'scarcity_index': scarcity_index,
                    'competition_index': competition_index,
                    'market_concentration': market_concentration,
                    'supply_adequacy': supply_adequacy,
                    'supply_demand_ratio': people_with_skill / demand_movements if demand_movements > 0 else float('inf')
                }
        
        print(f"   → Calculated supply/demand for {len(skill_supply_demand_results):,} skills")
        return skill_supply_demand_results
        
    except Exception as e:
        print(f"   ⚠️ Skills supply/demand analysis failed: {str(e)}")
        return {}

def categorize_supply_demand_dynamics(supply_demand_data):
    """Categorize supply/demand into business-friendly labels"""
    scarcity = supply_demand_data.get('scarcity_index', 1)
    adequacy = supply_demand_data.get('supply_adequacy', 1)
    
    if scarcity > 5 and adequacy < 0.5:
        return "Critical Shortage"
    elif scarcity > 2 and adequacy < 0.8:
        return "Supply Constrained"
    elif 0.8 <= adequacy <= 1.2:
        return "Balanced Market"
    elif adequacy > 2:
        return "Oversupplied"
                else:
        return "Emerging Demand"

# D. JOB OPPORTUNITY BREADTH INTELLIGENCE (Simplified Transferability)
# =============================================================================

def calculate_job_opportunity_breadth_analysis(conn):
    """
    Calculate Job Opportunity Breadth - simple, direct measurement of transferability
    
    Answers: "How many job profiles use this skill?" (0-100% scale)
    
    Returns:
        Dict with opportunity breadth metrics
    """
    print("🎯 Calculating Job Opportunity Breadth Analysis...")
    
    try:
        # Simple query: count job profiles that use each skill
        opportunity_query = """
        SELECT s.Skill_Name, s.Skill_ID,
               COUNT(DISTINCT js.JobProfileID) as job_profiles_with_skill
        FROM skills s
        JOIN job_skills js ON s.Skill_ID = js.Skill_ID
        GROUP BY s.Skill_Name, s.Skill_ID
        """
        
        skill_usage_data = pd.read_sql_query(opportunity_query, conn)
        
        # Get total job profiles in enterprise
        total_profiles_query = "SELECT COUNT(DISTINCT JobProfileID) as total FROM jobs"
        total_profiles = pd.read_sql_query(total_profiles_query, conn).iloc[0]['total']
        
        print(f"   → Total job profiles in enterprise: {total_profiles:,}")
        
        skill_opportunity_results = {}
        
        for _, row in skill_usage_data.iterrows():
            skill_name = row['Skill_Name']
            profiles_with_skill = row['job_profiles_with_skill']
            
            # Calculate opportunity breadth percentage (0-100%)
            opportunity_breadth_score = (profiles_with_skill / total_profiles * 100) if total_profiles > 0 else 0
            
            skill_opportunity_results[skill_name] = {
                'job_profiles_with_skill': int(profiles_with_skill),
                'total_job_profiles': int(total_profiles),
                'opportunity_breadth_score': round(opportunity_breadth_score, 2),
                'opportunity_breadth_percentage': f"{opportunity_breadth_score:.1f}%"
            }
        
        print(f"   → Calculated opportunity breadth for {len(skill_opportunity_results):,} skills")
        return skill_opportunity_results
        
    except Exception as e:
        print(f"   ⚠️ Job opportunity breadth analysis failed: {str(e)}")
        return {}

def categorize_opportunity_breadth(breadth_score):
    """Categorize opportunity breadth into business-friendly labels"""
    
    if breadth_score >= 20:
        return "Universal Skill"        # 20%+ of jobs
    elif breadth_score >= 10:
        return "Cross-Functional Skill" # 10-20% of jobs  
    elif breadth_score >= 5:
        return "Transferable Skill"     # 5-10% of jobs
    elif breadth_score >= 1:
        return "Specialized Skill"      # 1-5% of jobs
    else:
        return "Niche Skill"           # <1% of jobs

# =============================================================================
# ENHANCED SKILL INTELLIGENCE COMPOSITE SCORING
# =============================================================================

def calculate_composite_skill_intelligence_score(skill_data):
    """
    Calculate composite skill intelligence score combining all four analysis areas
    
    Similar to Movement Engine's approach: single score + percentile ranking
    """
    
    # Component weights (keeping it simple like Movement Engine)
    INTELLIGENCE_WEIGHTS = {
        'rarity_component': 25,        # 25% - How rare/valuable is this skill
        'velocity_component': 25,      # 25% - Is demand growing or declining
        'network_component': 25,       # 25% - How connected/bridging is this skill
        'transferability_component': 25 # 25% - How broadly applicable is this skill
    }
    
    # Component 1: Rarity Intelligence (0-25 points)
    rarity_category = skill_data.get('rarity_category', 'Universal')
    rarity_weights = {'Rare': 1.0, 'Uncommon': 0.8, 'Common': 0.5, 'Universal': 0.2}
    rarity_component = rarity_weights.get(rarity_category, 0.2) * INTELLIGENCE_WEIGHTS['rarity_component']
    
    # Component 2: Velocity Intelligence (0-25 points)
    velocity_category = skill_data.get('velocity_category', 'Stable Demand')
    velocity_weights = {
        'Accelerating Demand': 1.0, 'Growing Momentum': 0.8, 'Stable Demand': 0.6,
        'Volatile Demand': 0.4, 'Declining Momentum': 0.2, 'Steep Decline': 0.0
    }
    velocity_component = velocity_weights.get(velocity_category, 0.6) * INTELLIGENCE_WEIGHTS['velocity_component']
    
    # Component 3: Network Intelligence (0-25 points)
    network_score = skill_data.get('network_centrality_score', 0) / 100  # Normalize to 0-1
    network_component = network_score * INTELLIGENCE_WEIGHTS['network_component']
    
    # Component 4: Job Opportunity Breadth Intelligence (0-25 points)
    # Simple normalization: opportunity breadth is already 0-100% scale
    opportunity_breadth_score = skill_data.get('opportunity_breadth_score', 0)
    # Normalize to 0-1 scale (opportunity breadth is already percentage)
    transferability_normalized = min(1.0, opportunity_breadth_score / 100)
    
    transferability_component = transferability_normalized * INTELLIGENCE_WEIGHTS['transferability_component']
    
    # Total composite score (0-100)
    composite_score = rarity_component + velocity_component + network_component + transferability_component
    
    return {
        'composite_intelligence_score': round(composite_score, 1),
        'components': {
            'rarity': round(rarity_component, 1),
            'velocity': round(velocity_component, 1),
            'network': round(network_component, 1),
            'transferability': round(transferability_component, 1)
        }
    }

def get_dynamic_skill_intelligence_tier(score, percentile_rank, score_distribution):
    """
    Dynamic tier classification with full transparency
    
    Returns tier in format: "Strategic (Top 10%, 99.2%)"
    - Tier name (Strategic, High-Value, etc.)
    - Bracket definition (Top 10%, Top 25%, etc.)  
    - Exact percentile (99.2%)
    """
    
    # Calculate dynamic thresholds based on actual data distribution
    thresholds = {
        'strategic': score_distribution.quantile(0.90),    # Top 10%
        'high_value': score_distribution.quantile(0.75),   # Top 25%
        'valuable': score_distribution.quantile(0.60),     # Top 40%
        'standard': score_distribution.quantile(0.40),     # Top 60%
        'emerging': score_distribution.quantile(0.25),     # Top 75%
    }
    
    # Determine tier and format with full transparency
    if score >= thresholds['strategic']:
        return f"Strategic (Top 10%, {percentile_rank:.1f}%)"
    elif score >= thresholds['high_value']:
        return f"High-Value (Top 25%, {percentile_rank:.1f}%)"
    elif score >= thresholds['valuable']:
        return f"Valuable (Top 40%, {percentile_rank:.1f}%)"
    elif score >= thresholds['standard']:
        return f"Standard (Top 60%, {percentile_rank:.1f}%)"
    elif score >= thresholds['emerging']:
        return f"Emerging (Top 75%, {percentile_rank:.1f}%)"
            else:
        return f"Niche (Bottom 25%, {percentile_rank:.1f}%)"

def generate_tier_decoder_ring(score_distribution):
    """
    Generate the 'decoder ring' showing all tier thresholds for transparency
    """
    thresholds = {
        'strategic': score_distribution.quantile(0.90),
        'high_value': score_distribution.quantile(0.75),
        'valuable': score_distribution.quantile(0.60),
        'standard': score_distribution.quantile(0.40),
        'emerging': score_distribution.quantile(0.25),
        'niche': score_distribution.min()
    }
    
    total_count = len(score_distribution)
    min_score = score_distribution.min()
    max_score = score_distribution.max()
    avg_score = score_distribution.mean()
    
    decoder_output = []
    decoder_output.append("📊 TIER DECODER RING (Thresholds for This Analysis):")
    decoder_output.append("-" * 70)
    decoder_output.append(f"Strategic Skills (Top 10%):     Score ≥{thresholds['strategic']:.1f}  ({int(total_count * 0.10)} skills)")
    decoder_output.append(f"High-Value Skills (Top 25%):    Score ≥{thresholds['high_value']:.1f}  ({int(total_count * 0.25)} skills)")
    decoder_output.append(f"Valuable Skills (Top 40%):      Score ≥{thresholds['valuable']:.1f}  ({int(total_count * 0.40)} skills)")
    decoder_output.append(f"Standard Skills (Top 60%):      Score ≥{thresholds['standard']:.1f}  ({int(total_count * 0.60)} skills)")
    decoder_output.append(f"Emerging Skills (Top 75%):      Score ≥{thresholds['emerging']:.1f}  ({int(total_count * 0.75)} skills)")
    decoder_output.append(f"Niche Skills (Bottom 25%):      Score <{thresholds['emerging']:.1f}  ({int(total_count * 0.25)} skills)")
    decoder_output.append("")
    decoder_output.append(f"Score Distribution: Min={min_score:.1f}, Max={max_score:.1f}, Average={avg_score:.1f}")
    
    return decoder_output

def calculate_comprehensive_skill_mobility(conn):
    """Calculate skill mobility for ALL active skills in the enterprise"""
    print("   → Loading comprehensive skill mobility network...")
    
    try:
        # Get all movement data
        movement_query = """
        WITH unique_positions AS (
            SELECT DISTINCT [Position Number], JobProfileID
            FROM positions
            WHERE JobProfileID IS NOT NULL
        )
        SELECT 
            mf.movement_year,
            p_from.JobProfileID as JobProfileID_from,
            p_to.JobProfileID as JobProfileID_to,
            mf.movement_count
        FROM movement_fact mf
        JOIN unique_positions p_from ON mf.from_position = p_from.[Position Number]
        JOIN unique_positions p_to ON mf.to_position = p_to.[Position Number]
        WHERE mf.movement_year >= 2020
        AND mf.movement_count > 0
        """
        
        movement_df = pd.read_sql_query(movement_query, conn)
        print(f"   → Loaded {len(movement_df):,} movement records")
        
        # Get job-skill mappings
        job_skills_query = """
        SELECT js.JobProfileID, js.Skill_ID, s.Skill_Name, s.Category
        FROM job_skills js
        JOIN skills s ON js.Skill_ID = s.Skill_ID
        """
        job_skills_df = pd.read_sql_query(job_skills_query, conn)
        print(f"   → Loaded {len(job_skills_df):,} job-skill mappings")
        
        # Focus on active skills
        active_job_profiles = set(movement_df['JobProfileID_from'].unique()) | set(movement_df['JobProfileID_to'].unique())
        active_job_skills = job_skills_df[job_skills_df['JobProfileID'].isin(active_job_profiles)].copy()
        skills_in_use = active_job_skills['Skill_ID'].unique()
        
        print(f"   → Calculating mobility for {len(skills_in_use):,} active skills...")
        
        all_skill_mobility = {}
        
        # Process skills in batches to manage memory
        batch_size = 100
        processed_count = 0
        
        for i in range(0, len(skills_in_use), batch_size):
            skill_batch = skills_in_use[i:i + batch_size]
            
            for skill_id in skill_batch:
                try:
                skill_info = active_job_skills[active_job_skills['Skill_ID'] == skill_id].iloc[0]
                skill_name = skill_info['Skill_Name']
                
                # Get job profiles that have this skill
                jobs_with_skill = active_job_skills[active_job_skills['Skill_ID'] == skill_id]['JobProfileID'].unique()
                
                # Get movements FROM jobs with this skill
                from_movements = movement_df[movement_df['JobProfileID_from'].isin(jobs_with_skill)]
                
                if len(from_movements) == 0:
                    continue
                
                # Get skills in destination jobs
                destination_job_skills = from_movements.merge(
                    active_job_skills[['JobProfileID', 'Skill_ID', 'Category']], 
                    left_on='JobProfileID_to', 
                    right_on='JobProfileID', 
                    how='inner'
                )
                
                # Filter out the same skill
                destination_other_skills = destination_job_skills[destination_job_skills['Skill_ID'] != skill_id]
                
                    if len(destination_other_skills) > 5:  # Minimum threshold for analysis
                        # Calculate mobility metrics
                    destination_skills = destination_other_skills['Skill_ID'].value_counts()
                    diversity_score = calculate_diversity_score(destination_skills.to_dict())
                    unique_destinations = len(destination_skills)
                    total_movements = destination_other_skills['movement_count'].sum()
                    
                    source_category = skill_info['Category']
                    cross_category_moves = destination_other_skills[
                        destination_other_skills['Category'] != source_category
                    ]['movement_count'].sum()
                    cross_category_rate = cross_category_moves / total_movements if total_movements > 0 else 0
                    
                    skill_metrics = {
                        'diversity_score': diversity_score,
                        'unique_destinations': unique_destinations,
                        'total_movements': total_movements,
                        'cross_category_rate': cross_category_rate
                    }
                    
                    mobility_analysis = calculate_skill_mobility_score(skill_metrics)
                    
                    all_skill_mobility[skill_name] = {
                        'mobility_score': mobility_analysis['mobility_score'],
                        'mobility_tier': mobility_analysis['mobility_tier'],
                        'unique_destinations': unique_destinations,
                        'total_transitions': total_movements,
                        'diversity_score': diversity_score,
                        'cross_category_rate': cross_category_rate
                    }
                        
                        processed_count += 1
                        
                except Exception as e:
                    print(f"   ⚠️ Skipped skill {skill_id}: {str(e)[:50]}")
                    continue
            
            # Memory cleanup
            if i % (batch_size * 5) == 0:
                import gc
                gc.collect()
        
        print(f"   → Completed mobility analysis for {len(all_skill_mobility):,} skills")
        return all_skill_mobility
        
    except Exception as e:
        print(f"   ⚠️ Comprehensive skill mobility failed: {str(e)}")
        return {}

# =============================================================================
# MAIN ANALYSIS FUNCTION
# =============================================================================

def analyze_all_skills_with_advanced_intelligence(output_filename: Optional[str] = None):
    """
    Enhanced version of analyze_all_skills with the four new intelligence modules
    
    Returns comprehensive skill intelligence similar to Movement Engine's approach
    """
    print("🎯 COMPREHENSIVE SKILLS INTELLIGENCE ANALYSIS")
    print("="*80)
    print("📝 Analyzing active skills with 4 advanced intelligence modules:")
    print("   A. Temporal Skills Intelligence (velocity, momentum, acceleration)")
    print("   B. Skills Network Analysis (centrality, clustering, bridges)")  
    print("   C. Skills Supply/Demand Intelligence (scarcity, competition, market dynamics)")
    print("   D. Job Opportunity Breadth Intelligence (simple transferability: job profile count)")
    
    conn = connect_database()
    
    try:
        # 1. Load base skill data (existing)
        skill_universe = load_skill_universe(conn)
        skill_mobility_data = calculate_comprehensive_skill_mobility(conn)
        skill_trends = calculate_skill_growth_trends(conn, skill_universe)
        
        # 2. Calculate advanced intelligence modules
        print("\n🧠 CALCULATING ADVANCED INTELLIGENCE MODULES:")
        velocity_results = calculate_skills_velocity_analysis(conn)
        network_results = calculate_skills_network_analysis(conn)
        supply_demand_results = calculate_skills_supply_demand_analysis(conn)
        transferability_results = calculate_job_opportunity_breadth_analysis(conn)
        
        # 3. Filter to active skills and integrate all intelligence
        active_skill_names = set(skill_mobility_data.keys())
        active_skill_universe = skill_universe[
            skill_universe['Skill_Name'].isin(active_skill_names)
        ].copy()
        
        print(f"\n🔍 INTEGRATING INTELLIGENCE FOR {len(active_skill_universe):,} ACTIVE SKILLS:")
        
        # If no active skills found, fall back to top skills by prevalence
        if len(active_skill_universe) == 0:
            print("   ⚠️ No skills found with mobility data, using top 100 skills by prevalence")
            active_skill_universe = skill_universe.nlargest(100, 'prevalence_percentage')
            print(f"   → Fallback to {len(active_skill_universe):,} most prevalent skills")
        
        enhanced_skills = []
        
        for _, skill_row in active_skill_universe.iterrows():
                skill_id = skill_row['Skill_ID']
            skill_name = skill_row['Skill_Name']
            
            # Base skill data
            base_data = {
                    'skill_id': skill_id,
                'skill_name': skill_name,
                    'skill_category': skill_row.get('Category', 'Unknown'),
                    'skill_type': skill_row.get('SkillType', 'Unknown'),
                    'current_prevalence_percent': round(skill_row['prevalence_percentage'], 2),
                    'rarity_category': skill_row['rarity_category'],
                    'total_job_profiles_using': int(skill_row['profiles_using_skill']),
            }
            
            # Existing intelligence
            mobility_data = skill_mobility_data.get(skill_name, {})
            trend_data = skill_trends.get(skill_id, {}) if skill_trends else {}
            
            # New intelligence modules
            velocity_data = velocity_results.get(skill_name, {})
            network_data = network_results.get(skill_name, {})
            supply_demand_data = supply_demand_results.get(skill_name, {})
            transferability_data = transferability_results.get(skill_name, {})
            
            # Create comprehensive skill record
            enhanced_record = {
                **base_data,
                
                # Existing intelligence
                'skill_mobility_score': round(mobility_data.get('mobility_score', 0), 1),
                'skill_mobility_tier': mobility_data.get('mobility_tier', 'No Data'),
                'growth_trend_5yr': round(trend_data.get('growth_trend_5yr', 0) * 100, 1),
                'growth_category': categorize_growth_trend(trend_data.get('growth_trend_5yr', 0)) if skill_trends else "Data Unavailable",
                
                # A. Temporal Intelligence
                'velocity_momentum': round(velocity_data.get('momentum', 0), 1),
                'velocity_category': categorize_skill_velocity(velocity_data),
                'demand_volatility': round(velocity_data.get('demand_volatility', 0), 1),
                
                # B. Network Intelligence  
                'network_centrality': network_data.get('degree_centrality', 0),
                'network_diversity': round(network_data.get('network_diversity', 0), 3),
                'network_centrality_score': min(100, 
                    math.log10(max(1, network_data.get('weighted_centrality', 1))) * 10),  # Log scale normalization
                
                # C. Supply/Demand Intelligence
                'internal_supply': supply_demand_data.get('internal_supply', 0),
                'internal_demand': supply_demand_data.get('internal_demand', 0),
                'scarcity_index': round(supply_demand_data.get('scarcity_index', 0), 2),
                'supply_demand_category': categorize_supply_demand_dynamics(supply_demand_data),
                
                # D. Job Opportunity Breadth Intelligence
                'opportunity_breadth_score': round(transferability_data.get('opportunity_breadth_score', 0), 2),
                'opportunity_breadth_category': categorize_opportunity_breadth(transferability_data.get('opportunity_breadth_score', 0)),
                'job_profiles_with_skill': transferability_data.get('job_profiles_with_skill', 0),
                'total_job_profiles': transferability_data.get('total_job_profiles', 0),
            }
            
            # Calculate composite intelligence score (like Movement Engine)
            composite_analysis = calculate_composite_skill_intelligence_score(enhanced_record)
            enhanced_record['composite_intelligence_score'] = composite_analysis['composite_intelligence_score']
            
            # Add component breakdown
            enhanced_record.update({
                f'component_{k}': v for k, v in composite_analysis['components'].items()
            })
            
            enhanced_skills.append(enhanced_record)
        
        # Create results DataFrame and calculate percentile rankings (like Movement Engine)
        results_df = pd.DataFrame(enhanced_skills)
        
        if len(results_df) == 0:
            print("❌ No skills could be processed - returning empty DataFrame")
            return pd.DataFrame()
        
        # Calculate percentile rankings for composite score
        from scipy.stats import percentileofscore
        results_df['intelligence_percentile'] = [
            percentileofscore(results_df['composite_intelligence_score'], score, kind='rank')
            for score in results_df['composite_intelligence_score']
        ]
        
        # Sort by composite intelligence score (like Movement Engine)
        results_df = results_df.sort_values('composite_intelligence_score', ascending=False)
        
        # Apply dynamic tier classification with full transparency
        score_distribution = results_df['composite_intelligence_score']
        results_df['intelligence_tier'] = [
            get_dynamic_skill_intelligence_tier(score, percentile, score_distribution)
            for score, percentile in zip(results_df['composite_intelligence_score'], results_df['intelligence_percentile'])
        ]
        
        # Display the decoder ring for full transparency
        decoder_ring = generate_tier_decoder_ring(score_distribution)
        print("\n" + "\n".join(decoder_ring))
        
        # Output comprehensive summary
        print(f"\n📊 COMPREHENSIVE SKILLS INTELLIGENCE SUMMARY:")
        print("-" * 60)
        print(f"✅ Skills analyzed: {len(results_df):,}")
        print(f"   → Intelligence modules: 4 (Temporal, Network, Supply/Demand, Job Opportunity Breadth)")
        print(f"   → Composite scoring: 0-100 scale with percentile rankings")
        print(f"   → Top 10% skills: {len(results_df[results_df['intelligence_percentile'] >= 90]):,}")
        print(f"   → High-value skills (>75th percentile): {len(results_df[results_df['intelligence_percentile'] >= 75]):,}")
        
        # Show top strategic skills (like Movement Engine top pathways)
        print(f"\n🏆 TOP 10 STRATEGIC SKILLS (by Composite Intelligence):")
        print("-" * 130)
        header = f"{'Skill Name':<35} {'Score':<8} {'Tier':<35} {'Key Strengths':<50}"
        print(header)
        print("-" * 130)
        
        for _, skill in results_df.head(10).iterrows():
            skill_name = skill['skill_name'][:34]
            score = f"{skill['composite_intelligence_score']:.1f}"
            tier = skill['intelligence_tier'][:34]  # Accommodate longer tier format
            
            # Identify key strengths (adjusted thresholds for 0-25 component scale)
            strengths = []
            if skill['component_rarity'] >= 15: strengths.append("Rare")           # Top 60% threshold
            if skill['component_velocity'] >= 15: strengths.append("Growing")      # Top 60% threshold
            if skill['component_network'] >= 15: strengths.append("Connected")     # Top 60% threshold  
            if skill['component_transferability'] >= 15: strengths.append("Transferable")  # Top 60% threshold
            key_strengths = ", ".join(strengths)[:49]
            
            print(f"{skill_name:<35} {score:<8} {tier:<35} {key_strengths:<50}")
        
        # Save comprehensive results
                if output_filename:
                    output_path = Path(output_filename)
                else:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = Path(f"comprehensive_skills_intelligence_{timestamp}.csv")
        
                    results_df.to_csv(output_path, index=False)
        print(f"\n💾 Comprehensive analysis saved to: {output_path}")
        print(f"   📊 {len(results_df):,} skills with full intelligence metrics")
            
            return results_df
            
    finally:
        conn.close()
        print("🔒 Database connection closed")

# =============================================================================
# COMPREHENSIVE TESTING SUITE
# =============================================================================

def test_database_schema():
    """Test database schema and data quality like movement_analysis_engine.py"""
    print("🔍 TESTING DATABASE SCHEMA AND DATA QUALITY")
    print("="*60)
    
    conn = connect_database()
    
    try:
        print_memory_status()
        
        # Test 1: Check positions table and JobProfileID mapping (critical issue)
        print("\n1️⃣ Testing Position-to-Job Mapping (Critical for Skills Analysis)...")
        
        position_mapping_query = """
        WITH unique_positions AS (
            SELECT DISTINCT [Position Number], JobProfileID
            FROM positions
            WHERE JobProfileID IS NOT NULL AND JobProfileID != ''
        )
        SELECT COUNT(*) as valid_mappings,
               COUNT(DISTINCT [Position Number]) as unique_positions,
               COUNT(DISTINCT JobProfileID) as unique_jobs
        FROM unique_positions
        """
        
        mapping_stats = pd.read_sql_query(position_mapping_query, conn)
        print(f"   → Valid position-job mappings: {mapping_stats.iloc[0]['valid_mappings']:,}")
        print(f"   → Unique positions with jobs: {mapping_stats.iloc[0]['unique_positions']:,}")
        print(f"   → Unique job profiles: {mapping_stats.iloc[0]['unique_jobs']:,}")
        
        if mapping_stats.iloc[0]['valid_mappings'] == 0:
            print("   ❌ CRITICAL: No valid position-to-job mappings found!")
            print("   → This explains why we get 0 active skills")
            
            # Investigate the positions table structure
            positions_sample_query = """
            SELECT [Position Number], JobProfileID, [Position Name]
            FROM positions 
            LIMIT 5
            """
            positions_sample = pd.read_sql_query(positions_sample_query, conn)
            print(f"   → Sample positions data:")
            print(positions_sample.to_string())
            
            return False
        else:
            print("   ✅ Position-to-job mappings look good")
        
        # Test 2: Check movement_fact structure (like movement_analysis_engine.py)
        print("\n2️⃣ Testing Movement Fact Table Structure...")
        
        movement_sample_query = """
        SELECT movement_year, movement_month, from_position, to_position, movement_count
        FROM movement_fact 
        WHERE movement_year >= 2020
        LIMIT 5
        """
        
        movement_sample = pd.read_sql_query(movement_sample_query, conn)
        print(f"   → Sample movement data:")
        print(movement_sample.to_string())
        
        # Test 3: Check job_skills relationships
        print("\n3️⃣ Testing Job-Skills Relationships...")
        
        job_skills_stats_query = """
        SELECT COUNT(*) as total_relationships,
               COUNT(DISTINCT JobProfileID) as jobs_with_skills,
               COUNT(DISTINCT Skill_ID) as skills_used
        FROM job_skills
        """
        
        job_skills_stats = pd.read_sql_query(job_skills_stats_query, conn)
        print(f"   → Total job-skill relationships: {job_skills_stats.iloc[0]['total_relationships']:,}")
        print(f"   → Jobs with skills: {job_skills_stats.iloc[0]['jobs_with_skills']:,}")
        print(f"   → Skills in use: {job_skills_stats.iloc[0]['skills_used']:,}")
        
        print_memory_status()
        return True
        
    except Exception as e:
        print(f"   ❌ Database schema test failed: {str(e)}")
        return False
    finally:
        conn.close()

def test_movement_to_skills_pipeline():
    """Test the pipeline from movement data to skills analysis"""
    print("\n🔄 TESTING MOVEMENT-TO-SKILLS PIPELINE")
        print("="*60)
    
    conn = connect_database()
    
    try:
        # Use the same pattern as movement_analysis_engine.py
        print("\n1️⃣ Testing Movement-to-Job Mapping (Movement Engine Pattern)...")
        
        movement_fact_query = """
        WITH unique_positions AS (
            SELECT DISTINCT [Position Number], JobProfileID
            FROM positions
            WHERE JobProfileID IS NOT NULL AND JobProfileID != ''
        )
        SELECT 
            mf.movement_year,
            mf.from_position,
            mf.to_position,
            mf.movement_count,
            p_from.JobProfileID as JobProfileID_from,
            p_to.JobProfileID as JobProfileID_to
        FROM movement_fact mf
        JOIN unique_positions p_from ON mf.from_position = p_from.[Position Number]
        JOIN unique_positions p_to ON mf.to_position = p_to.[Position Number]
        WHERE mf.movement_year >= 2020
        LIMIT 10
        """
        
        movement_with_jobs = pd.read_sql_query(movement_fact_query, conn)
        print(f"   → Movement records with job mappings: {len(movement_with_jobs):,}")
        
        if len(movement_with_jobs) == 0:
            print("   ❌ No movement records could be mapped to job profiles")
            return False
        else:
            print("   ✅ Movement-to-job mapping successful")
            print(f"   → Sample data:")
            print(movement_with_jobs.head(3).to_string())
        
        # Test 2: Check skills for these job profiles
        print("\n2️⃣ Testing Skills for Movement Job Profiles...")
        
        job_profiles_in_movement = set(movement_with_jobs['JobProfileID_from'].unique()) | set(movement_with_jobs['JobProfileID_to'].unique())
        print(f"   → Unique job profiles in movements: {len(job_profiles_in_movement):,}")
        
        # Get skills for these job profiles
        job_profiles_list = "', '".join(job_profiles_in_movement)
        skills_for_movement_jobs_query = f"""
        SELECT js.JobProfileID, js.Skill_ID, s.Skill_Name
        FROM job_skills js
        JOIN skills s ON js.Skill_ID = s.Skill_ID
        WHERE js.JobProfileID IN ('{job_profiles_list}')
        LIMIT 100
        """
        
        skills_for_movement = pd.read_sql_query(skills_for_movement_jobs_query, conn)
        print(f"   → Skills found for movement job profiles: {len(skills_for_movement):,}")
        
        if len(skills_for_movement) == 0:
            print("   ❌ No skills found for job profiles in movements")
            return False
        else:
            print("   ✅ Skills found for movement job profiles")
            unique_skills = skills_for_movement['Skill_ID'].nunique()
            print(f"   → Unique skills: {unique_skills:,}")
        
        print_memory_status()
        return True
        
    except Exception as e:
        print(f"   ❌ Movement-to-skills pipeline test failed: {str(e)}")
        return False
    finally:
        conn.close()

def test_individual_modules():
    """Test each intelligence module individually with improved error handling"""
    print("\n🧪 TESTING INDIVIDUAL INTELLIGENCE MODULES")
        print("="*60)
    
    conn = connect_database()
    
    try:
        print_memory_status()
        
        # Test 1: Load skill universe
        print("\n1️⃣ Testing Skill Universe Loading...")
        try:
            skill_universe = load_skill_universe(conn)
            print(f"   ✅ Loaded {len(skill_universe):,} skills")
            print(f"   → Skill categories: {skill_universe['Category'].nunique():,}")
            print(f"   → Skill types: {skill_universe['SkillType'].value_counts().to_dict()}")
        except Exception as e:
            print(f"   ❌ Skill universe loading failed: {str(e)}")
            return False
        
        # Test 2: Velocity Analysis
        print("\n2️⃣ Testing Velocity Analysis...")
        try:
            velocity_results = calculate_skills_velocity_analysis(conn, lookback_years=2)  # Reduced years
            print(f"   ✅ Velocity analysis: {len(velocity_results):,} skills")
            if velocity_results:
                sample_skill = list(velocity_results.keys())[0]
                print(f"   → Sample metrics for '{sample_skill}': {velocity_results[sample_skill]}")
        except Exception as e:
            print(f"   ❌ Velocity analysis failed: {str(e)}")
        
        # Test 3: Network Analysis
        print("\n3️⃣ Testing Network Analysis...")
        try:
            network_results = calculate_skills_network_analysis(conn)
            print(f"   ✅ Network analysis: {len(network_results):,} skills")
            if network_results:
                sample_skill = list(network_results.keys())[0]
                print(f"   → Sample metrics for '{sample_skill}': {network_results[sample_skill]}")
        except Exception as e:
            print(f"   ❌ Network analysis failed: {str(e)}")
        
        # Test 4: Supply/Demand Analysis
        print("\n4️⃣ Testing Supply/Demand Analysis...")
        try:
            supply_demand_results = calculate_skills_supply_demand_analysis(conn)
            print(f"   ✅ Supply/demand analysis: {len(supply_demand_results):,} skills")
            if supply_demand_results:
                sample_skill = list(supply_demand_results.keys())[0]
                print(f"   → Sample metrics for '{sample_skill}': {supply_demand_results[sample_skill]}")
        except Exception as e:
            print(f"   ❌ Supply/demand analysis failed: {str(e)}")
        
        # Test 5: Job Opportunity Breadth Analysis
        print("\n5️⃣ Testing Job Opportunity Breadth Analysis...")
        try:
            transferability_results = calculate_job_opportunity_breadth_analysis(conn)
            print(f"   ✅ Job opportunity breadth analysis: {len(transferability_results):,} skills")
            if transferability_results:
                sample_skill = list(transferability_results.keys())[0]
                print(f"   → Sample metrics for '{sample_skill}': {transferability_results[sample_skill]}")
        except Exception as e:
            print(f"   ❌ Job opportunity breadth analysis failed: {str(e)}")
        
        print_memory_status()
        print(f"\n🎉 MODULE TESTING COMPLETED!")
        
    finally:
        conn.close()
        print("🔒 Database connection closed")

def test_score_normalization():
    """Test that composite scores are properly normalized to 0-100 range"""
    print("\n🔢 TESTING SCORE NORMALIZATION")
    print("="*50)
    
    try:
        print("🧮 Running quick analysis to check score ranges...")
        
        # Run analysis on a small sample
        results = analyze_all_skills_with_advanced_intelligence()
        
        if len(results) > 0:
            # Check score ranges
            min_score = results['composite_intelligence_score'].min()
            max_score = results['composite_intelligence_score'].max()
            mean_score = results['composite_intelligence_score'].mean()
            
            print(f"\n📊 Score Range Analysis:")
            print(f"   → Minimum score: {min_score:.1f}")
            print(f"   → Maximum score: {max_score:.1f}")
            print(f"   → Average score: {mean_score:.1f}")
            print(f"   → Expected range: 0-100")
            
            # Check if scores are in reasonable range
            if max_score <= 100 and min_score >= 0:
                print("   ✅ Scores are properly normalized!")
            else:
                print("   ❌ Scores still outside expected 0-100 range")
            
            # Check tier distribution
            tier_counts = results['intelligence_tier'].value_counts()
            print(f"\n🏆 Tier Distribution:")
            for tier, count in tier_counts.head(5).items():
                print(f"   → {tier}: {count}")
            
            return max_score <= 100 and min_score >= 0
        else:
            print("❌ No results to analyze")
            return False
            
    except Exception as e:
        print(f"❌ Score normalization test failed: {str(e)}")
        return False

def test_tier_distribution():
    """Test tier distribution after threshold adjustments"""
    print("\n🏆 TESTING TIER DISTRIBUTION")
    print("="*50)
    
    try:
        print("📊 Running analysis to check tier distribution...")
        
        results = analyze_all_skills_with_advanced_intelligence()
        
        if len(results) > 0:
            # Analyze tier distribution
            tier_counts = results['intelligence_tier'].value_counts()
            total_skills = len(results)
            
            print(f"\n🎯 Tier Distribution (Total: {total_skills:,} skills):")
            print("-" * 60)
            for tier, count in tier_counts.items():
                percentage = (count / total_skills) * 100
                print(f"   → {tier}: {count:,} skills ({percentage:.1f}%)")
            
            # Check if we have good distribution
            strategic_count = tier_counts.get("Strategic Skill (Top 10%)", 0)
            high_value_count = tier_counts.get("High-Value Skill (Top 25%)", 0)
            
            print(f"\n📈 Distribution Quality Check:")
            if strategic_count > 0:
                print(f"   ✅ Strategic skills identified: {strategic_count}")
            else:
                print("   ⚠️ No strategic skills identified")
                
            if high_value_count > 0:
                print(f"   ✅ High-value skills identified: {high_value_count}")
            else:
                print("   ⚠️ No high-value skills identified")
            
            return strategic_count > 0 and high_value_count > 0
        else:
            print("❌ No results to analyze")
            return False
            
    except Exception as e:
        print(f"❌ Tier distribution test failed: {str(e)}")
        return False

def test_full_skills_intelligence():
    """Test the full comprehensive skills intelligence analysis"""
    print("\n🎯 TESTING FULL COMPREHENSIVE SKILLS INTELLIGENCE")
    print("="*60)
    
    try:
        print("🚀 Running comprehensive analysis with all 4 intelligence modules...")
        print("   → This includes: Temporal, Network, Supply/Demand, Transferability")
        
        results = analyze_all_skills_with_advanced_intelligence("test_comprehensive_skills_intelligence.csv")
        
        if len(results) > 0:
            print(f"\n✅ COMPREHENSIVE ANALYSIS SUCCESSFUL!")
            print(f"   → Skills analyzed: {len(results):,}")
            print(f"   → Columns generated: {len(results.columns):,}")
            
            # Show top 5 skills by composite intelligence score
            if 'composite_intelligence_score' in results.columns:
            top_skills = results.head(5)
                print(f"\n🏆 TOP 5 STRATEGIC SKILLS:")
            for _, skill in top_skills.iterrows():
                    name = skill['skill_name'][:40]
                    score = skill['composite_intelligence_score']
                    tier = skill.get('intelligence_tier', 'Unknown')
                    print(f"   → {name}: {score:.1f} ({tier})")
            
            # Show intelligence module coverage
            modules_working = []
            if results['velocity_momentum'].notna().sum() > 0:
                modules_working.append("✅ Temporal Intelligence")
            else:
                modules_working.append("❌ Temporal Intelligence")
                
            if results['network_centrality'].notna().sum() > 0:
                modules_working.append("✅ Network Intelligence")
            else:
                modules_working.append("❌ Network Intelligence")
                
            if results['scarcity_index'].notna().sum() > 0:
                modules_working.append("✅ Supply/Demand Intelligence")
            else:
                modules_working.append("❌ Supply/Demand Intelligence")
                
            if results['transferability_score'].notna().sum() > 0:
                modules_working.append("✅ Transferability Intelligence")
            else:
                modules_working.append("❌ Transferability Intelligence")
            
            print(f"\n📊 Intelligence Module Status:")
            for module in modules_working:
                print(f"   {module}")
            
            return True
        else:
            print("❌ Comprehensive analysis returned empty results")
            return False
            
    except Exception as e:
        print(f"❌ Comprehensive analysis failed: {str(e)}")
        return False

def run_comprehensive_tests():
    """Main test execution following movement_analysis_engine.py patterns"""
    print("🚀 SKILLS INTELLIGENCE ENGINE - COMPREHENSIVE TESTING")
    print("="*80)
    print("Based on patterns from movement_analysis_engine.py")
    
    # Step 1: Test database schema and data quality
    schema_ok = test_database_schema()
    
    if not schema_ok:
        print("\n❌ CRITICAL SCHEMA ISSUES DETECTED - STOPPING TESTS")
        return
    
    # Step 2: Test movement-to-skills pipeline
    pipeline_ok = test_movement_to_skills_pipeline()
    
    if not pipeline_ok:
        print("\n⚠️ PIPELINE ISSUES DETECTED - CONTINUING WITH LIMITED TESTING")
    
    # Step 3: Test individual modules
    test_individual_modules()
    
    # Step 4: Test score normalization
    if pipeline_ok:
        normalization_ok = test_score_normalization()
        
        # Step 5: Test tier distribution
        if normalization_ok:
            tier_ok = test_tier_distribution()
            
            # Step 6: Test full comprehensive analysis
            if tier_ok:
                test_full_skills_intelligence()
    
    print(f"\n🏁 TESTING COMPLETE")
    print_memory_status()

# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    print("🎯 COMPLETE SKILLS INTELLIGENCE ENGINE")
    print("="*80)
    print("🔬 Running comprehensive tests and analysis...")
    print("📊 This will test all 4 intelligence modules and generate complete analysis")
    print()
    
    # Run comprehensive testing and analysis
    run_comprehensive_tests()
    
    print(f"\n🎉 COMPLETE! Skills Intelligence Engine is ready for dual-engine integration.")
    print(f"📁 Check the generated CSV files for detailed results.") 