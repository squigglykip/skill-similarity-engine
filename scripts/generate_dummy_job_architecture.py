#!/usr/bin/env python3
"""
Generate Dummy Job Architecture Data

This script creates realistic dummy job architecture data matching the comprehensive schema
from job_arch_schema.json. Used for development when real data cannot
be transferred to personal devices.

Based on updated schema: 3,098 job profile records with 16 columns:
- JobID: Related job identifier (384 unique values)
- Job: Human-readable job name (384 unique values)
- JobProfileID: Unique identifier (3,098 unique values, 100% unique)
- JobProfile: Human-readable job profile name (3,098 unique values, 100% unique)
- ProfileTitleSuffix: Career level/suffix (16 categories)
- ManagementLevel: Group level classification (8 categories: Group 1-7, Group NA)
- JobSubFunctionID: Job sub-function identifier (105 unique values)
- JobSubFunction: Job sub-function name (105 unique values)
- JobFunctionID: Job function identifier (~20-25 unique values)
- JobFunction: Job function name (~20-25 unique values)
- JobCategoryID: Job category identifier (4 categories: JC1, JC2, JC3, JC10)
- JobCategory: Job category name (4 categories)
- Customer Facing: Customer interaction flag (Customer Facing/Non-Customer Facing)
- is Banker: Banking role flag (Banker/Non-Banker)
- Executive Leadership Group: Executive flag (mostly null, 195 records have value)
- Accountability Scope: Accountability type (Direct/Supports, mostly null)

NEW: JobFunction and JobFunctionID are hierarchically above JobSubFunction,
with multiple subfunctions mapping to each function (fewer unique values).
"""

import pandas as pd
import numpy as np
import random
from pathlib import Path
from typing import List, Dict, Any, Optional

# Set random seed for reproducible dummy data
random.seed(42)
np.random.seed(42)

# Configuration
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "job_architecture"
JOB_SKILL_MAPPING_FILE = Path(__file__).parent.parent / "data" / "input_data" / "job_skill_mapping.csv"

def load_actual_job_profile_ids():
    """Load the actual JobProfileIDs from the job-skill mapping file"""
    print(f"📊 Loading JobProfileIDs from job-skill mapping...")
    
    if not JOB_SKILL_MAPPING_FILE.exists():
        print(f"❌ ERROR: Job-skill mapping file not found at {JOB_SKILL_MAPPING_FILE}")
        print(f"   Falling back to hardcoded list...")
        return FALLBACK_JOB_PROFILE_IDS
    
    try:
        # Read the job-skill mapping file and extract unique JobProfileIDs
        df = pd.read_csv(JOB_SKILL_MAPPING_FILE)
        actual_job_profile_ids = df['JobProfileID'].unique().tolist()
        
        print(f"✅ Successfully loaded {len(actual_job_profile_ids)} unique JobProfileIDs from mapping file")
        print(f"   Sample IDs: {actual_job_profile_ids[:5]}")
        
        return actual_job_profile_ids
        
    except Exception as e:
        print(f"❌ ERROR loading job-skill mapping file: {e}")
        print(f"   Falling back to hardcoded list...")
        return FALLBACK_JOB_PROFILE_IDS

# Fallback JobProfileIDs (original hardcoded list) in case file loading fails
FALLBACK_JOB_PROFILE_IDS = [
    'R0001.5', 'R0001.6', 'R0002.0', 'R0002.1', 'R0002.3', 'R0002.2',
    'R0002.4', 'R0003.2', 'R0003.0', 'R0005.1', 'R0007.1', 'R0009.0',
    'R0009.1', 'R0010.1', 'R0022.6', 'R0023.3', 'R0023.2', 'R0025.3',
    'R0025.2', 'R0025.5', 'R0030.4', 'R0037.0', 'R0037.3', 'R0038.6',
    'R0039.4', 'R0039.0', 'R0039.2', 'R0039.3', 'R0039.1', 'R0039.5',
    'R0040.2', 'R0040.0', 'R0040.3', 'R0040.1', 'R0040.5', 'R0041.3',
    'R0041.0', 'R0041.1', 'R0041.2', 'R0041.4', 'R0042.6', 'R0043.3',
    'R0043.5', 'R0043.0', 'R0043.2', 'R0043.4', 'R0043.1', 'R0044.3',
    'R0044.4', 'R0044.0', 'R0044.2', 'R0045.0', 'R0045.3', 'R0045.4',
    'R0045.5', 'R0045.2', 'R0046.6', 'R0047.2', 'R0047.0', 'R0047.4',
    'R0049.3', 'R0049.4', 'R0050.0', 'R0050.4', 'R0050.3', 'R0050.5',
    'R0050.2', 'R0050.1', 'R0051.6', 'R0052.3', 'R0053.0', 'R0053.4',
    'R0053.3', 'R0053.1', 'R0053.5', 'R0053.2', 'R0054.2', 'R0054.4',
    'R0054.3', 'R0054.0', 'R0054.5', 'R0058.0', 'R0058.5', 'R0067.7',
    'R0069.7', 'R0070.7', 'R0072.7', 'R0073.7', 'R0074.7', 'R0075.3',
    'R0075.2', 'R0075.4', 'R0075.5', 'R0078.6', 'R0079.4', 'R0079.3',
    'R0079.5', 'R0079.0', 'R0079.2', 'R0080.6', 'R0081.6', 'R0082.3',
    'R0082.4', 'R0082.5', 'R0083.2', 'R0083.5', 'R0083.3', 'R0084.5',
    'R0084.2', 'R0084.3', 'R0084.0', 'R0084.4', 'R0086.6', 'R0087.6',
    'R0088.3', 'R0088.4', 'R0088.0', 'R0088.5', 'R0090.2', 'R0090.0',
    'R0090.3', 'R0091.3', 'R0091.2', 'R0091.4', 'R0091.0', 'R0091.1',
    'R0092.3', 'R0092.1', 'R0092.4', 'R0092.0', 'R0092.2', 'R0092.5',
    'R0094.0', 'R0094.4', 'R0094.2', 'R0094.1', 'R0094.3', 'R0094.5',
    'R0096.4', 'R0096.0', 'R0096.3', 'R0096.2', 'R0097.4', 'R0097.0',
    'R0097.2', 'R0097.3', 'R0097.5', 'R0099.3', 'R0099.5', 'R0099.2',
    'R0100.2', 'R0102.3', 'R0102.5', 'R0103.2', 'R0103.3', 'R0103.4',
    'R0103.5', 'R0103.0', 'R0104.3', 'R0111.6', 'R0116.2', 'R0116.3',
    'R0116.4', 'R0172.5', 'R0172.3', 'R0181.2', 'R0181.3', 'R0187.1',
    'R0187.3', 'R0187.2', 'R0187.0', 'R0187.4', 'R0187.5', 'R0191.3',
    'R0202.1', 'R0202.5', 'R0202.0', 'R0207.3', 'R0208.3', 'R0208.4',
    'R0208.1', 'R0208.2', 'R0208.0', 'R0210.0', 'R0211.3', 'R0211.5',
    'R0212.3', 'R0212.0', 'R0213.3', 'R0213.4', 'R0213.2', 'R0213.1',
    'R0213.0', 'R0214.5', 'R0214.4', 'R0214.3', 'R0214.2', 'R0214.0',
    'R0217.3', 'R0217.4', 'R0217.0', 'R0217.2', 'R0218.3', 'R0218.4',
    'R0218.1', 'R0218.0', 'R0218.5', 'R0218.2', 'R0220.4', 'R0222.3',
    'R0222.5', 'R0222.2', 'R0222.4', 'R0222.0', 'R0223.5', 'R0223.4',
    'R0223.3', 'R0223.0', 'R0223.2', 'R0224.5', 'R0224.0', 'R0224.2',
    'R0224.4', 'R0225.4', 'R0225.0', 'R0228.4', 'R0228.0', 'R0228.3',
    'R0228.5', 'R0228.2', 'R0230.3', 'R0230.4', 'R0230.0', 'R0230.2',
    'R0231.3', 'R0231.2', 'R0231.4', 'R0231.5', 'R0231.1', 'R0233.3',
    'R0233.2', 'R0233.0', 'R0233.4', 'R0234.3', 'R0234.4', 'R0234.0',
    'R0235.3', 'R0235.0', 'R0235.2', 'R0235.5', 'R0235.4', 'R0236.4',
    'R0236.2', 'R0236.3', 'R0237.3', 'R0237.4', 'R0237.2', 'R0237.5',
    'R0237.1', 'R0237.0', 'R0238.0', 'R0238.4', 'R0238.2', 'R0238.3',
    'R0238.5', 'R0239.0', 'R0239.5', 'R0239.4', 'R0239.3', 'R0239.2',
    'R0240.4', 'R0240.0', 'R0240.3', 'R0240.5', 'R0240.2', 'R0241.0',
    'R0241.3', 'R0241.4', 'R0241.2', 'R0241.5', 'R0242.3', 'R0242.0',
    'R0242.2', 'R0242.4', 'R0242.5', 'R0243.6', 'R0246.4', 'R0248.6',
    'R0249.5', 'R0249.3', 'R0249.4', 'R0249.2', 'R0251.6', 'R0252.6',
    'R0252.5', 'R0253.2', 'R0253.1', 'R0253.0', 'R0253.3', 'R0253.4',
    'R0254.4', 'R0254.5', 'R0254.0', 'R0254.3', 'R0254.2', 'R0254.1',
    'R0255.4', 'R0255.0', 'R0256.4', 'R0256.2', 'R0256.3', 'R0257.6',
    'R0258.2', 'R0258.3', 'R0258.0', 'R0258.5', 'R0259.6', 'R0262.0',
    'R0262.1', 'R0262.5', 'R0262.4', 'R0263.4', 'R0263.5', 'R0263.3',
    'R0263.2', 'R0264.6', 'R0266.3', 'R0266.4', 'R0267.3', 'R0268.1',
    'R0268.3', 'R0268.2', 'R0268.4', 'R0268.0', 'R0270.2', 'R0270.1',
    'R0270.3', 'R0270.4', 'R0270.5', 'R0270.0', 'R0276.5', 'R0276.2',
    'R0276.1', 'R0276.3', 'R0276.4', 'R0277.2', 'R0277.3', 'R0277.5',
    'R0279.5', 'R0279.6', 'R0280.5', 'R0280.2', 'R0280.3', 'R0281.0',
    'R0281.5', 'R0281.2', 'R0281.1', 'R0281.4', 'R0281.3', 'R0282.6',
    'R0283.3', 'R0283.5', 'R0283.4', 'R0283.2', 'R0284.5', 'R0285.5',
    'R0285.4', 'R0286.3', 'R0286.5', 'R0286.4', 'R0286.0', 'R0287.4',
    'R0287.3', 'R0287.2', 'R0288.6', 'R0289.2', 'R0289.4', 'R0289.5',
    'R0290.5', 'R0290.3', 'R0290.0', 'R0291.6', 'R0292.5', 'R0292.3',
    'R0292.4', 'R0292.2', 'R0292.0', 'R0293.3', 'R0293.2', 'R0293.0',
    'R0293.4', 'R0293.5', 'R0296.3', 'R0298.5', 'R0298.3', 'R0298.2',
    'R0302.4', 'R0302.3', 'R0302.5', 'R0303.2', 'R0303.3', 'R0303.4',
    'R0303.0', 'R0303.5', 'R0304.3', 'R0304.2', 'R0304.4', 'R0304.0',
    'R0304.5', 'R0305.3', 'R0305.4', 'R0305.2', 'R0305.0', 'R0305.5',
    'R0306.3', 'R0306.4', 'R0306.0', 'R0307.6', 'R0308.4', 'R0308.3',
    'R0308.2', 'R0308.5', 'R0309.6', 'R0310.3', 'R0310.5', 'R0310.4',
    'R0313.4', 'R0313.2', 'R0313.3', 'R0313.0', 'R0313.5', 'R0315.0',
    'R0315.6', 'R0316.5', 'R0316.2', 'R0316.4', 'R0317.0', 'R0317.2',
    'R0317.3', 'R0317.4', 'R0318.5', 'R0318.4', 'R0319.4', 'R0319.5',
    'R0320.1', 'R0320.3', 'R0320.5', 'R0320.0', 'R0320.4', 'R0320.2',
    'R0321.3', 'R0321.0', 'R0323.0', 'R0323.5', 'R0323.2', 'R0323.3',
    'R0323.4', 'R0325.5', 'R0325.4', 'R0328.4', 'R0328.0', 'R0329.6',
    'R0330.5', 'R0330.0', 'R0330.4', 'R0331.4', 'R0331.0', 'R0331.2',
    'R0332.3', 'R0332.4', 'R0332.2', 'R0333.3', 'R0333.4', 'R0333.2',
    'R0333.0', 'R0333.5', 'R0335.0', 'R0335.4', 'R0335.2', 'R0335.3',
    'R0341.0', 'R0341.3', 'R0341.4', 'R0341.5', 'R0343.2', 'R0343.0',
    'R0343.4', 'R0343.3', 'R0346.4', 'R0346.0', 'R0346.3', 'R0346.2',
    'R0347.2', 'R0347.0', 'R0347.3', 'R0347.4', 'R0348.0', 'R0348.3',
    'R0348.4', 'R0348.2', 'R0348.1', 'R0348.5', 'R0349.2', 'R0349.4',
    'R0349.0', 'R0349.3', 'R0349.5', 'R0349.1', 'R0350.2', 'R0350.4',
    'R0350.0', 'R0350.3', 'R0350.5', 'R0350.1', 'R0351.5', 'R0351.2',
    'R0351.3', 'R0351.4', 'R0352.0', 'R0352.3', 'R0352.4', 'R0352.2',
    'R0354.3', 'R0354.0', 'R0354.2', 'R0354.1', 'R0354.4', 'R0354.5',
    'R0355.0', 'R0355.3', 'R0355.2', 'R0355.4', 'R0355.5', 'R0362.4',
    'R0362.0', 'R0362.3', 'R0365.4', 'R0367.0', 'R0367.1', 'R0367.2',
    'R0367.3', 'R0368.3', 'R0368.1', 'R0368.2', 'R0368.4', 'R0368.0',
    'R0374.6', 'R0376.0', 'R0376.3', 'R0376.4', 'R0377.3', 'R0377.2',
    'R0377.0', 'R0377.4', 'R0377.5', 'R0380.0', 'R0380.4', 'R0380.3',
    'R0380.2', 'R0380.5', 'R0381.6', 'R0384.6', 'R0385.6', 'R0386.6',
    'R0387.6', 'R0388.6', 'R0389.6', 'R0399.6', 'R0400.6', 'R0401.6',
    'R0402.6', 'R0403.6', 'R0404.6', 'R0405.6', 'R0406.6', 'R0407.6',
    'R0408.6', 'R0409.6', 'R0411.6', 'R0417.6', 'R0418.6', 'R0419.6',
    'R0420.6', 'R0420.0', 'R0424.3', 'R0424.4', 'R0424.0', 'R0424.2',
    'R0424.5', 'R0425.1', 'R0425.0', 'R0426.0', 'R0426.5', 'R0426.2',
    'R0427.2', 'R0427.3', 'R0427.0', 'R0427.5', 'R0427.4', 'R0427.1',
    'R0428.3', 'R0428.4', 'R0429.4', 'R0429.5', 'R0429.3', 'R0433.5',
    'R0433.4', 'R0433.3', 'R0433.0', 'R0433.2', 'R0434.3', 'R0434.2',
    'R0434.5', 'R0434.4', 'R0434.0', 'R0435.3', 'R0435.4', 'R0435.0',
    'R0435.5', 'R0436.0', 'R0436.3', 'R0437.4', 'R0437.5', 'R0437.3',
    'R0437.2', 'R0437.0', 'R0438.2', 'R0438.3', 'R0438.4', 'R0438.0',
    'R0438.5', 'R0439.0', 'R0439.3', 'R0439.2', 'R0439.4', 'R0439.5',
    'R0440.4', 'R0440.3', 'R0440.2', 'R0440.5', 'R0440.0', 'R0441.2',
    'R0441.3', 'R0441.0', 'R0441.5', 'R0441.4', 'R0441.1', 'R0442.0',
    'R0442.3', 'R0442.5', 'R0442.2', 'R0442.4', 'R0444.6', 'R0446.6',
    'R0447.6', 'R0449.3', 'R0451.3', 'R0452.6', 'R0453.2', 'R0453.0',
    'R0453.1', 'R0454.3', 'R0454.5', 'R0454.0', 'R0454.4', 'R0454.2',
    'R0456.5', 'R0456.0', 'R0456.2', 'R0456.4', 'R0456.3', 'R0456.1',
    'R0457.3', 'R0457.4', 'R0457.2', 'R0457.0', 'R0457.5', 'R0458.4',
    'R0463.3', 'R0463.4', 'R0463.5', 'R0463.2', 'R0464.2', 'R0465.0',
    'R0465.3', 'R0465.5', 'R0465.4', 'R0466.2', 'R0466.0', 'R0466.4',
    'R0466.3', 'R0466.5', 'R0467.0', 'R0467.3', 'R0467.5', 'R0467.2',
    'R0467.4', 'R0468.3', 'R0469.4', 'R0469.0', 'R0470.0', 'R0471.0',
    'R0472.2', 'R0472.3', 'R0472.0', 'R0472.5', 'R0473.2', 'R0474.2',
    'R0475.2', 'R0475.3', 'R0475.4', 'R0475.5', 'R0476.5', 'R0476.2',
    'R0477.0'
]

# Expanded data structures based on comprehensive schema

# ProfileTitleSuffix categories (16 categories from schema)
PROFILE_TITLE_SUFFIXES = [
    'Advisor', 'Analyst', 'Associate', 'Consultant', 'Group Executive',
    'Head of', 'I', 'II', 'III', 'Lead Consultant', 'Manager',
    'Senior Consultant', 'Senior Manager', 'Team Lead', 'Team Member', 'UNGRADED'
]

# ManagementLevel categories (8 categories from schema)
MANAGEMENT_LEVELS = [
    'Group 1', 'Group 2', 'Group 3', 'Group 4', 'Group 5', 'Group 6', 'Group 7', 'Group NA'
]

# JobCategory mapping (4 categories from schema)
JOB_CATEGORIES = {
    'JC1': 'Enabling',
    'JC2': 'Support', 
    'JC3': 'Revenue Generating',
    'JC10': 'Executive & General Management'
}

# Customer Facing and Banker flags
CUSTOMER_FACING_OPTIONS = ['Customer Facing', 'Non-Customer Facing']
BANKER_OPTIONS = ['Banker', 'Non-Banker']

# Executive Leadership Group (mostly null, only 195 records have value)
EXECUTIVE_LEADERSHIP_GROUP = 'Executive Leadership Group'

# Accountability Scope (mostly null, 164 Supports + 117 Direct)
ACCOUNTABILITY_SCOPE_OPTIONS = ['Direct', 'Supports']

# Job Functions (higher level than subfunctions, ~20-25 unique values)
JOB_FUNCTIONS = {
    'JF001': 'Technology & Engineering',
    'JF002': 'Risk Management',
    'JF003': 'Finance & Treasury',
    'JF004': 'Customer Relations',
    'JF005': 'Operations & Processing',
    'JF006': 'Executive Leadership',
    'JF007': 'Human Resources',
    'JF008': 'Legal & Compliance',
    'JF009': 'Marketing & Communications',
    'JF010': 'Business Development',
    'JF011': 'Investment Management',
    'JF012': 'Banking Services',
    'JF013': 'Research & Analysis',
    'JF014': 'Project Management',
    'JF015': 'Audit & Assurance',
    'JF016': 'Data & Analytics',
    'JF017': 'Security & Fraud',
    'JF018': 'Support Services',
    'JF019': 'Strategy & Planning',
    'JF020': 'Training & Development',
    'JF021': 'Quality Management',
    'JF022': 'Facilities & Administration'
}

# Hierarchical mapping: JobSubFunction -> JobFunctionID
SUBFUNCTION_TO_FUNCTION_MAPPING = {
    # Technology & Engineering
    'Technology Infrastructure': 'JF001',
    'Data & Analytics': 'JF016',
    'Software Engineering': 'JF001',
    'Systems Analysis': 'JF001',
    'Database Administration': 'JF001',
    'Network Administration': 'JF001',
    'Application Support': 'JF001',
    'Help Desk': 'JF001',
    'Technical Support': 'JF001',
    'Cloud Computing': 'JF001',
    'Machine Learning': 'JF016',
    'Artificial Intelligence': 'JF016',
    'Business Intelligence': 'JF016',
    
    # Risk Management
    'Risk Management': 'JF002',
    'Credit Risk Assessment': 'JF002',
    'Operational Risk': 'JF002',
    'Market Risk': 'JF002',
    'Model Validation': 'JF002',
    'Stress Testing': 'JF002',
    'Basel Compliance': 'JF002',
    'Regulatory Capital': 'JF002',
    
    # Finance & Treasury
    'Corporate Finance': 'JF003',
    'Treasury Operations': 'JF003',
    'Liquidity Management': 'JF003',
    'Financial Planning': 'JF003',
    'Budgeting & Forecasting': 'JF003',
    'Management Accounting': 'JF003',
    'Financial Reporting': 'JF003',
    'Tax Services': 'JF003',
    'Quantitative Analysis': 'JF013',
    'Statistical Analysis': 'JF013',
    
    # Customer Relations
    'Customer Service Operations': 'JF004',
    'Customer Experience': 'JF004',
    'Relationship Management': 'JF004',
    'Account Management': 'JF004',
    'Sales': 'JF004',
    
    # Banking Services
    'Wealth Management': 'JF012',
    'Business Banking': 'JF012',
    'Digital Banking': 'JF012',
    'Retail Banking': 'JF012',
    'Private Banking': 'JF012',
    'Investment Banking': 'JF012',
    'Corporate Banking': 'JF012',
    
    # Operations & Processing
    'Payment Systems': 'JF005',
    'Settlement Operations': 'JF005',
    'Trade Finance': 'JF005',
    'Foreign Exchange': 'JF005',
    'Derivatives Trading': 'JF005',
    'Fixed Income & Equities Trading': 'JF005',
    'Custody': 'JF005',
    'Investment Operations': 'JF005',
    'Fund Administration': 'JF005',
    
    # Investment Management
    'Asset Management': 'JF011',
    'Portfolio Management': 'JF011',
    'Superannuation': 'JF011',
    'Insurance Services': 'JF011',
    'Actuarial Services': 'JF011',
    'Pension Administration': 'JF011',
    'Trustee Services': 'JF011',
    'Fiduciary Services': 'JF011',
    
    # Research & Analysis
    'Equity Research': 'JF013',
    'Fixed Income Research': 'JF013',
    'Economic Research': 'JF013',
    
    # Legal & Compliance
    'Compliance & Regulatory': 'JF008',
    'Legal Services': 'JF008',
    'Anti-Money Laundering': 'JF008',
    'Know Your Customer': 'JF008',
    'Regulatory Reporting': 'JF008',
    'Financial Crime': 'JF008',
    
    # Security & Fraud
    'Cybersecurity': 'JF017',
    'Information Security': 'JF017',
    'Physical Security': 'JF017',
    'Fraud Prevention': 'JF017',
    
    # Executive Leadership
    'Executive: Corporate Functions': 'JF006',
    'General and Executive Support': 'JF006',
    
    # Human Resources
    'Human Resources': 'JF007',
    'Learning & Development': 'JF020',
    'Talent Acquisition': 'JF007',
    'Employee Relations': 'JF007',
    'Compensation & Benefits': 'JF007',
    'Organisational Development': 'JF007',
    
    # Strategy & Planning
    'Strategy & Planning': 'JF019',
    'Business Development': 'JF010',
    
    # Project Management
    'Project Management': 'JF014',
    'Program Management': 'JF014',
    'Change Management': 'JF014',
    'Business Analysis': 'JF014',
    'Process Improvement': 'JF021',
    
    # Marketing & Communications
    'Marketing': 'JF009',
    'Brand Management': 'JF009',
    'Digital Marketing': 'JF009',
    'Communications': 'JF009',
    'Corporate Affairs': 'JF009',
    
    # Audit & Assurance
    'Audit & Assurance': 'JF015',
    'Internal Audit': 'JF015',
    'External Audit': 'JF015',
    'Quality Assurance': 'JF021',
    
    # Support Services
    'Business Services': 'JF018',
    'Vendor Management': 'JF018',
    'Procurement': 'JF018',
    'Facilities Management': 'JF022',
    'Real Estate': 'JF022',
    'Environmental Services': 'JF022',
    'Health & Safety': 'JF022',
    'Emergency Management': 'JF022',
    'Business Continuity': 'JF022',
    'Disaster Recovery': 'JF022',
    
    # Data & Analytics
    'Data Governance': 'JF016',
    'Data Management': 'JF016',
    
    # Product & Innovation
    'Product Management': 'JF010',
    
    # Graduate & Training
    'Graduate Program': 'JF020'
}

# Expanded job sub-functions (105 unique values in real data)
JOB_SUB_FUNCTIONS = [
    'Business Services', 'General and Executive Support', 'Graduate Program',
    'Corporate Finance', 'Executive: Corporate Functions', 'Fixed Income & Equities Trading',
    'Product Management', 'Custody', 'Risk Management', 'Compliance & Regulatory',
    'Technology Infrastructure', 'Data & Analytics', 'Customer Service Operations',
    'Wealth Management', 'Business Banking', 'Digital Banking', 'Credit Risk Assessment',
    'Operational Risk', 'Market Risk', 'Liquidity Management', 'Treasury Operations',
    'Investment Banking', 'Corporate Banking', 'Retail Banking', 'Private Banking',
    'Asset Management', 'Superannuation', 'Insurance Services', 'Payment Systems',
    'Settlement Operations', 'Trade Finance', 'Foreign Exchange', 'Derivatives Trading',
    'Equity Research', 'Fixed Income Research', 'Economic Research', 'Strategy & Planning',
    'Human Resources', 'Learning & Development', 'Talent Acquisition', 'Employee Relations',
    'Compensation & Benefits', 'Organisational Development', 'Change Management',
    'Project Management', 'Program Management', 'Business Analysis', 'Process Improvement',
    'Quality Assurance', 'Audit & Assurance', 'Internal Audit', 'External Audit',
    'Legal Services', 'Corporate Affairs', 'Communications', 'Marketing',
    'Brand Management', 'Digital Marketing', 'Customer Experience', 'Sales',
    'Relationship Management', 'Account Management', 'Business Development',
    'Cybersecurity', 'Information Security', 'Physical Security', 'Fraud Prevention',
    'Anti-Money Laundering', 'Know Your Customer', 'Regulatory Reporting',
    'Financial Crime', 'Data Governance', 'Data Management', 'Business Intelligence',
    'Machine Learning', 'Artificial Intelligence', 'Cloud Computing', 'Software Engineering',
    'Systems Analysis', 'Database Administration', 'Network Administration',
    'Application Support', 'Help Desk', 'Technical Support', 'Vendor Management',
    'Procurement', 'Facilities Management', 'Real Estate', 'Environmental Services',
    'Health & Safety', 'Emergency Management', 'Business Continuity', 'Disaster Recovery',
    'Financial Planning', 'Budgeting & Forecasting', 'Management Accounting',
    'Financial Reporting', 'Tax Services', 'Regulatory Capital', 'Basel Compliance',
    'Stress Testing', 'Model Validation', 'Quantitative Analysis', 'Statistical Analysis',
    'Actuarial Services', 'Pension Administration', 'Investment Operations',
    'Portfolio Management', 'Fund Administration', 'Trustee Services', 'Fiduciary Services'
]

# Banking-specific role categories for generating realistic job combinations
BANKING_ROLE_CATEGORIES = {
    'Technology & Digital': {
        'roles': ['Software Engineer', 'Data Scientist', 'Cybersecurity Analyst', 'Digital Product Manager', 'Cloud Architect'],
        'banker_likelihood': 0.1,
        'customer_facing_likelihood': 0.2,
        'job_category_weights': {'JC1': 0.4, 'JC2': 0.5, 'JC3': 0.1, 'JC10': 0.0}
    },
    'Risk & Compliance': {
        'roles': ['Risk Analyst', 'Compliance Officer', 'Credit Risk Manager', 'Operational Risk Specialist', 'Regulatory Specialist'],
        'banker_likelihood': 0.3,
        'customer_facing_likelihood': 0.1,
        'job_category_weights': {'JC1': 0.6, 'JC2': 0.3, 'JC3': 0.1, 'JC10': 0.0}
    },
    'Finance & Treasury': {
        'roles': ['Financial Analyst', 'Treasury Manager', 'Financial Controller', 'Investment Analyst', 'Budget Manager'],
        'banker_likelihood': 0.4,
        'customer_facing_likelihood': 0.2,
        'job_category_weights': {'JC1': 0.3, 'JC2': 0.4, 'JC3': 0.3, 'JC10': 0.0}
    },
    'Customer & Commercial': {
        'roles': ['Relationship Manager', 'Business Banker', 'Customer Service Representative', 'Sales Manager', 'Private Banker'],
        'banker_likelihood': 0.8,
        'customer_facing_likelihood': 0.9,
        'job_category_weights': {'JC1': 0.1, 'JC2': 0.2, 'JC3': 0.7, 'JC10': 0.0}
    },
    'Operations': {
        'roles': ['Operations Analyst', 'Settlement Officer', 'Trade Finance Specialist', 'Payment Systems Analyst', 'Process Manager'],
        'banker_likelihood': 0.5,
        'customer_facing_likelihood': 0.3,
        'job_category_weights': {'JC1': 0.2, 'JC2': 0.7, 'JC3': 0.1, 'JC10': 0.0}
    },
    'Executive & Leadership': {
        'roles': ['General Manager', 'Executive Director', 'Division Head', 'Regional Manager', 'Chief Officer'],
        'banker_likelihood': 0.7,
        'customer_facing_likelihood': 0.4,
        'job_category_weights': {'JC1': 0.1, 'JC2': 0.1, 'JC3': 0.2, 'JC10': 0.6}
    },
    'Support Functions': {
        'roles': ['HR Business Partner', 'Marketing Specialist', 'Legal Counsel', 'Project Manager', 'Business Analyst'],
        'banker_likelihood': 0.2,
        'customer_facing_likelihood': 0.2,
        'job_category_weights': {'JC1': 0.3, 'JC2': 0.6, 'JC3': 0.1, 'JC10': 0.0}
    }
}

def generate_job_sub_function_id():
    """Generate a realistic JobSubFunctionID"""
    return f"JF{random.randint(1, 999):04d}"

def get_job_function_from_subfunction(job_sub_function: str) -> tuple[str, str]:
    """
    Get JobFunctionID and JobFunction name from JobSubFunction.
    Returns (job_function_id, job_function_name)
    """
    # Get the function ID from the mapping
    job_function_id = SUBFUNCTION_TO_FUNCTION_MAPPING.get(job_sub_function)
    
    # If no mapping found, assign a default function based on common patterns
    if job_function_id is None:
        # Default fallback logic
        job_function_id = 'JF018'  # Support Services as default
    
    # Get the function name
    job_function_name = JOB_FUNCTIONS.get(job_function_id, 'Support Services')
    
    return job_function_id, job_function_name

def determine_management_level_weights(role_category: str, profile_suffix: str) -> Dict[str, float]:
    """Determine realistic management level weights based on role category and suffix"""
    
    # Executive roles get higher groups
    if 'Executive' in role_category or profile_suffix in ['Group Executive', 'Head of']:
        return {
            'Group 1': 0.05, 'Group 2': 0.1, 'Group 3': 0.15, 
            'Group 4': 0.2, 'Group 5': 0.2, 'Group 6': 0.15, 
            'Group 7': 0.1, 'Group NA': 0.05
        }
    
    # Senior roles get mid-higher groups
    elif profile_suffix in ['Senior Manager', 'Senior Consultant', 'Manager']:
        return {
            'Group 1': 0.1, 'Group 2': 0.25, 'Group 3': 0.3, 
            'Group 4': 0.2, 'Group 5': 0.1, 'Group 6': 0.03, 
            'Group 7': 0.01, 'Group NA': 0.01
        }
    
    # Junior roles get lower groups
    elif profile_suffix in ['Analyst', 'Associate', 'Team Member']:
        return {
            'Group 1': 0.4, 'Group 2': 0.35, 'Group 3': 0.15, 
            'Group 4': 0.07, 'Group 5': 0.02, 'Group 6': 0.005, 
            'Group 7': 0.005, 'Group NA': 0.02
        }
    
    # Default distribution
    else:
        return {
            'Group 1': 0.15, 'Group 2': 0.25, 'Group 3': 0.25, 
            'Group 4': 0.2, 'Group 5': 0.1, 'Group 6': 0.03, 
            'Group 7': 0.01, 'Group NA': 0.01
        }

def weighted_choice(choices: Dict[str, float]) -> str:
    """Make a weighted random choice from a dictionary of choices and probabilities"""
    items = list(choices.keys())
    weights = list(choices.values())
    # Normalize weights to ensure they sum to 1.0
    weights = np.array(weights)
    weights = weights / weights.sum()
    return np.random.choice(items, p=weights)

def generate_comprehensive_job_architecture_records(job_profile_ids):
    """Generate realistic job architecture records matching the exact 14-column schema"""
    
    records = []
    
    # Use the actual JobProfileIDs from the job-skill mapping file
    # Each JobProfileID gets exactly one record in the job architecture
    for job_profile_id in job_profile_ids:
            
        # Extract base role number for consistent JobID generation
        base_number = job_profile_id.split('.')[0]  # e.g., 'R0001' from 'R0001.5'
        
        # Assign role category (deterministic based on base ID for consistency)
        category_key = list(BANKING_ROLE_CATEGORIES.keys())[hash(base_number) % len(BANKING_ROLE_CATEGORIES)]
        role_category_info = BANKING_ROLE_CATEGORIES[category_key]
        
        # Generate base role from category
        base_role = np.random.choice(role_category_info['roles'])
        
        # Generate ProfileTitleSuffix
        profile_suffix = np.random.choice(PROFILE_TITLE_SUFFIXES)
        
        # Create JobProfile name (specific instance)
        if profile_suffix in ['I', 'II', 'III']:
            job_profile_name = f"{base_role} - {profile_suffix}"
        elif profile_suffix == 'UNGRADED':
            job_profile_name = f"{base_role} (Ungraded)"
        else:
            # Use the decimal part of the JobProfileID for uniqueness
            decimal_part = job_profile_id.split('.')[1] if '.' in job_profile_id else '1'
            job_profile_name = f"{base_role} - {decimal_part}"
        
        # Generate Job name (broader category, should have fewer unique values)
        job_name = base_role
        
        # Generate JobID (should have fewer unique values than JobProfileID)
        job_id = base_number  # Same base number, creating fewer unique JobIDs
        
        # Determine ManagementLevel based on role and suffix
        management_level_weights = determine_management_level_weights(category_key, profile_suffix)
        management_level = weighted_choice(management_level_weights)
        
        # Generate JobSubFunction and ID
        job_sub_function = np.random.choice(JOB_SUB_FUNCTIONS)
        job_sub_function_id = generate_job_sub_function_id()
        
        # Get JobFunction information from JobSubFunction (hierarchical relationship)
        job_function_id, job_function = get_job_function_from_subfunction(job_sub_function)
        
        # Determine JobCategory based on role category
        job_category_id = weighted_choice(role_category_info['job_category_weights'])
        job_category = JOB_CATEGORIES[job_category_id]
        
        # Determine Customer Facing based on category likelihood
        is_customer_facing = random.random() < role_category_info['customer_facing_likelihood']
        customer_facing = 'Customer Facing' if is_customer_facing else 'Non-Customer Facing'
        
        # Determine Banker status based on category likelihood
        is_banker_role = random.random() < role_category_info['banker_likelihood']
        is_banker = 'Banker' if is_banker_role else 'Non-Banker'
        
        # Executive Leadership Group (only ~6.3% have this value)
        executive_leadership = EXECUTIVE_LEADERSHIP_GROUP if random.random() < 0.063 else None
        
        # Accountability Scope (only ~9% have this value)
        if random.random() < 0.09:
            # 164 Supports vs 117 Direct in real data
            accountability_scope = 'Supports' if random.random() < 0.584 else 'Direct'
        else:
            accountability_scope = None
        
        # Customer Facing nulls (24 records, 0.77% of data)
        if random.random() < 0.0077:
            customer_facing = None
        
        # is Banker nulls (24 records, 0.77% of data)  
        if random.random() < 0.0077:
            is_banker = None
        
        record = {
            'JobID': job_id,
            'Job': job_name,
            'JobProfileID': job_profile_id,
            'JobProfile': job_profile_name,
            'ProfileTitleSuffix': profile_suffix,
            'ManagementLevel': management_level,
            'JobSubFunctionID': job_sub_function_id,
            'JobSubFunction': job_sub_function,
            'JobFunctionID': job_function_id,
            'JobFunction': job_function,
            'JobCategoryID': job_category_id,
            'JobCategory': job_category,
            'Customer Facing': customer_facing,
            'is Banker': is_banker,
            'Executive Leadership Group': executive_leadership,
            'Accountability Scope': accountability_scope
        }
        
        records.append(record)
    
    return records

def main():
    """Generate and save comprehensive dummy job architecture data"""
    
    print(f"Generating comprehensive dummy job architecture data...")
    print(f"Target schema: 16 columns (including JobFunction hierarchy)")
    
    # Load actual JobProfileIDs from job-skill mapping file
    actual_job_profile_ids = load_actual_job_profile_ids()
    print(f"Using {len(actual_job_profile_ids)} JobProfileIDs from job-skill mapping")
    
    # Generate the dataset
    job_arch_data = generate_comprehensive_job_architecture_records(actual_job_profile_ids)
    
    # Convert to DataFrame
    df = pd.DataFrame(job_arch_data)
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    output_file = OUTPUT_DIR / "dummy_job_architecture.csv"
    df.to_csv(output_file, index=False)
    
    print(f"\nGenerated comprehensive dummy job architecture data:")
    print(f"- Records: {len(df):,}")
    print(f"- Columns: {len(df.columns)} (target: 16)")
    print(f"- File: {output_file}")
    print(f"- Size: {output_file.stat().st_size / 1024:.1f} KB")
    
    # Print sample of the data
    print(f"\nSample data (first 5 rows):")
    print(df[['JobProfileID', 'JobProfile', 'JobSubFunction', 'JobFunction', 'JobCategory']].head())
    
    # Print schema validation
    print(f"\nSchema Validation:")
    print(f"Expected columns: JobID, Job, JobProfileID, JobProfile,")
    print(f"                  ProfileTitleSuffix, ManagementLevel, JobSubFunctionID, JobSubFunction,")
    print(f"                  JobFunctionID, JobFunction, JobCategoryID, JobCategory,")
    print(f"                  Customer Facing, is Banker, Executive Leadership Group, Accountability Scope")
    print(f"Actual columns ({len(df.columns)}): {', '.join(df.columns)}")
    
    # Verify exact match with schema
    expected_columns = [
        'JobID', 'Job', 'JobProfileID', 'JobProfile', 'ProfileTitleSuffix', 'ManagementLevel',
        'JobSubFunctionID', 'JobSubFunction', 'JobFunctionID', 'JobFunction', 'JobCategoryID', 'JobCategory', 
        'Customer Facing', 'is Banker', 'Executive Leadership Group', 'Accountability Scope'
    ]
    
    if list(df.columns) == expected_columns:
        print(f"✅ Schema matches updated specification exactly!")
    else:
        print(f"❌ Schema mismatch detected!")
        print(f"Missing: {set(expected_columns) - set(df.columns)}")
        print(f"Extra: {set(df.columns) - set(expected_columns)}")
    
    # Print key statistics matching the schema
    print(f"\nKey Statistics (including new JobFunction hierarchy):")
    print(f"- Unique JobIDs: {df['JobID'].nunique():,} (target: ~384)")
    print(f"- Unique Jobs: {df['Job'].nunique():,} (target: ~384)")
    print(f"- Unique JobProfileIDs: {df['JobProfileID'].nunique():,} (target: 3,098, 100% unique)")
    print(f"- Unique JobProfiles: {df['JobProfile'].nunique():,} (target: 3,098, 100% unique)")
    print(f"- ProfileTitleSuffix categories: {df['ProfileTitleSuffix'].nunique()} (target: 16)")
    print(f"- ManagementLevel categories: {df['ManagementLevel'].nunique()} (target: 8)")
    print(f"- JobSubFunctions: {df['JobSubFunction'].nunique()} (target: 105)")
    print(f"- JobFunctions: {df['JobFunction'].nunique()} (target: ~20-25)")
    print(f"- JobCategory categories: {df['JobCategory'].nunique()} (target: 4)")
    
    # Print distribution analysis
    print(f"\nDistribution Analysis:")
    print(f"\nProfileTitleSuffix (top 5):")
    for suffix, count in df['ProfileTitleSuffix'].value_counts().head().items():
        print(f"  - {suffix}: {count}")
    
    print(f"\nManagementLevel:")
    for level, count in df['ManagementLevel'].value_counts().items():
        print(f"  - {level}: {count}")
    
    print(f"\nJobCategory:")
    for category, count in df['JobCategory'].value_counts().items():
        print(f"  - {category}: {count}")
    
    print(f"\nJobFunction (top 10):")
    for function, count in df['JobFunction'].value_counts().head(10).items():
        print(f"  - {function}: {count}")
    
    print(f"\nCustomer Facing:")
    for facing, count in df['Customer Facing'].value_counts(dropna=False).items():
        print(f"  - {facing}: {count}")
    
    print(f"\nis Banker:")
    for banker, count in df['is Banker'].value_counts(dropna=False).items():
        print(f"  - {banker}: {count}")
    
    # Check for nulls in key fields
    exec_leadership_nulls = df['Executive Leadership Group'].isnull().sum()
    accountability_nulls = df['Accountability Scope'].isnull().sum()
    customer_facing_nulls = df['Customer Facing'].isnull().sum()
    banker_nulls = df['is Banker'].isnull().sum()
    
    print(f"\nNull Analysis:")
    print(f"- Executive Leadership Group nulls: {exec_leadership_nulls} ({exec_leadership_nulls/len(df)*100:.1f}%) - target: ~93.7%")
    print(f"- Accountability Scope nulls: {accountability_nulls} ({accountability_nulls/len(df)*100:.1f}%) - target: ~90.9%")
    print(f"- Customer Facing nulls: {customer_facing_nulls} ({customer_facing_nulls/len(df)*100:.1f}%) - target: ~0.77%")
    print(f"- is Banker nulls: {banker_nulls} ({banker_nulls/len(df)*100:.1f}%) - target: ~0.77%")
    
    # Print schema info
    print(f"\nDataFrame Info:")
    print(df.info())

if __name__ == "__main__":
    main() 