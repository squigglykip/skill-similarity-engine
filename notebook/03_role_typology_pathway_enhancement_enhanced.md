================================================================================
ENHANCED ROLE TYPOLOGY ANALYSIS & PATHWAY ENHANCEMENT V2.0
================================================================================
Job Profile Focus • Mobility Scoring • Defining Skills • Architectural Progression

✅ Connected to database: models/2025-Q3/workforce_intelligence.sqlite
🚀 ENHANCED ANALYSIS FEATURES V2.0:
   → Job Profile granularity (1,765 profiles vs 106 sub-functions)
   → Mobility Score gradient (0-100) replacing binary classification
   → Defining Skills feature based on NAB enterprise rarity
   → Architectural focus (career progression) vs organizational context
   → Multi-level analysis with enhanced pathway insights
   → Dataset scope: 121,165 movements, 40,673 positions, 38,524 skills
   → Time range: 2020 - 2025
💾 Memory Usage: 188.5 MB

================================================================================
ENHANCED DATA LOADING AND PREPARATION V2.0
================================================================================

📋 METHODOLOGY:
--------------------------------------------------

    Enhanced data loading with job profile focus and temporal handling:
    1. Load movement data from database (temporal aggregations preserved)
    2. Load job architecture, positions, and workforce context
    3. Enrich movements with full job profile and organizational context
    4. Apply recency weighting (40% decay rate - banking environment changes fast)
    5. Filter to current job profiles only (recommendations for existing roles)
    6. Deduplicate position mappings to prevent cartesian products
    7. Memory-efficient processing with enhanced context preservation


📁 Loading movement data from database table: movement_fact
📋 Column name normalization:
✅ Successfully loaded 121,165 records from movement_fact table
📅 Data range: 2020 - 2025
🔄 Enhanced data enrichment V2.0 with job profile focus and recency weighting...
🏢 Loaded workforce context: 43,096 records
🏢 Loaded jobs data: 1,765 job profiles
🏢 Loaded positions data: 43,096 position records
   → Found Division → organizational context
   → Found Business_Unit → organizational context
   → Enhanced position mapping: ['Position Number', 'JobProfileID', 'Division', 'Business_Unit']
   ⚠️  Found 2,423 duplicate position numbers - deduplicating...
   → Deduplicated from 43,096 to 40,673 positions
   → Removed 2,423 duplicate position records
   → Processing 121,165 records in chunks...
✅ Enhanced enriched dataset V2.0: 121,165 movement records
💾 Memory Usage: 392.2 MB
📊 Enhanced dataset V2.0: 121,165 enriched movement records
📅 Date range: 2020 - 2025
🔄 Applying data cleaning with recency weighting...
   → Initial records: 121,165
   → After dropping null JobProfileIDs: 27,555
   → Current job profiles available: 1,765
   → After job profile filtering: 27,312 (removed 243)
   → Data retention by year:
     2020: 15.7% retained
     2021: 17.1% retained
     2022: 22.5% retained
     2023: 26.8% retained
     2024: 33.3% retained
     2025: 29.2% retained
   → Overall retention: 22.5%
📊 Cleaned dataset V2.0: 27,312 weighted movement records
🔍 Available enhanced features (10): ['movement_count', 'avg_days_between', 'JobProfileID_from', 'JobProfileID_to', 'from_job_function', 'from_job_sub_function', 'from_job_category', 'from_management_level', 'from_division', 'from_business_unit']
💾 Memory Usage: 313.9 MB

================================================================================
ENTERPRISE SKILL RARITY ANALYSIS
================================================================================

📋 METHODOLOGY:
--------------------------------------------------

    Calculating defining skills based on NAB enterprise rarity:
    1. Calculate skill prevalence across all 1,765 job profiles
    2. Categorize skills by rarity (Rare <5%, Uncommon 5-20%, Common 20-50%, Universal >50%)
    3. Identify top 5 defining skills per job profile (rarest skills)
    4. Create skill-based differentiation profiles for career guidance


🎯 Calculating enterprise-wide skill rarity scores...
   → Total job profiles in enterprise: 1,765
   → Calculated rarity for 2,442 skills
   → Rarity distribution:
      Rare: 2,272 skills (93.0%)
      Uncommon: 140 skills (5.7%)
      Common: 28 skills (1.1%)
      Universal: 2 skills (0.1%)
🔍 Identifying defining skills per job profile...
   → Identified defining skills for 1,743 job profiles
✅ Skill rarity analysis completed
   → 2,442 skills analyzed
   → 1,743 job profiles with defining skills

🎯 EXAMPLE DEFINING SKILLS:

   📋 Executive Manager - 15:
      Total skills: 50, Rare skills: 35
      Defining skills:
        • Microsoft Access: 0.1% prevalence (Rare)
        • Predictive Statistics: 0.8% prevalence (Rare)
        • Managerial Finance: 1.1% prevalence (Rare)

   📋 Executive Manager - 18:
      Total skills: 56, Rare skills: 26
      Defining skills:
        • Predictive Statistics: 0.8% prevalence (Rare)
        • Managerial Finance: 1.1% prevalence (Rare)
        • Predictive Modeling: 1.1% prevalence (Rare)

   📋 Executive Manager - 19:
      Total skills: 50, Rare skills: 35
      Defining skills:
        • Microsoft Access: 0.1% prevalence (Rare)
        • Predictive Statistics: 0.8% prevalence (Rare)
        • Managerial Finance: 1.1% prevalence (Rare)

================================================================================
MULTI-DIMENSIONAL ROLE ANALYSIS WITH MOBILITY SCORING
================================================================================

📋 METHODOLOGY:
--------------------------------------------------

    Multi-dimensional role analysis with Mobility Score (0-100) and recency weighting:
    1. Job Profile Analysis (PRIMARY: 1,765 current job profiles)
    2. Job Sub-Function Analysis (SECONDARY: 106 broader patterns)
    3. Management Level Analysis (PROGRESSION: career advancement)
    4. Mobility Score calculation with recency-weighted transitions
    5. Architectural progression focus vs organizational context
    6. Temporal decay applied (recent moves weighted higher)



🔍 ANALYZING ARCHITECTURAL DIMENSION: Job Profile
   → Analysis dataset: 27,312 complete records
   → Processing 1060 Job Profile values...
   📊 Mobility Score Summary for Job Profile:
      Standard Mobility: 339 (32.0%) - Avg Score: 46.8
      Moderate Launchpad: 311 (29.3%) - Avg Score: 62.4
      Career Silo: 278 (26.2%) - Avg Score: 5.3
      Limited Mobility: 72 (6.8%) - Avg Score: 34.3
      Unknown: 38 (3.6%) - Avg Score: 54.9
      Strong Launchpad: 22 (2.1%) - Avg Score: 71.1

   🚀 TOP MOBILITY SCORES:
      • Business Banker: Small Business - 15: 74.1 (Strong Launchpad)
        Components: Diversity=22.8, Destinations=30.0, Volume=20.0, Cross-boundary=1.3
      • Business Banker: Middle Markets - 15: 73.1 (Strong Launchpad)
        Components: Diversity=22.7, Destinations=30.0, Volume=20.0, Cross-boundary=0.4
      • Personal Banker - 15: 72.4 (Strong Launchpad)
        Components: Diversity=35.5, Destinations=30.0, Volume=1.1, Cross-boundary=5.8
      • Administration Support - 00: 72.3 (Strong Launchpad)
        Components: Diversity=34.9, Destinations=30.0, Volume=0.8, Cross-boundary=6.7
      • Business Operations & Enablement - 20: 71.7 (Strong Launchpad)
        Components: Diversity=37.3, Destinations=30.0, Volume=0.5, Cross-boundary=3.9

   🔒 LOWEST MOBILITY SCORES:
      • Marketing - 15: 3.0 (Career Silo)
      • R0237.12: 3.0 (Career Silo)
      • Business Continuity Planning - 18: 3.0 (Career Silo)
      • Systems Security Management - 13: 3.0 (Career Silo)
      • Transformation - 12: 3.0 (Career Silo)
📊 Calculating enhanced movement probabilities for Job Profile...
   → Calculated 5,491 enhanced movement probabilities

🔍 ANALYZING ARCHITECTURAL DIMENSION: Job Sub-Function
   → Analysis dataset: 27,312 complete records
   → Processing 103 Job Sub-Function values...
   📊 Mobility Score Summary for Job Sub-Function:
      Moderate Launchpad: 52 (50.5%) - Avg Score: 62.1
      Standard Mobility: 25 (24.3%) - Avg Score: 47.3
      Strong Launchpad: 8 (7.8%) - Avg Score: 71.5
      Unknown: 6 (5.8%) - Avg Score: 56.8
      Limited Mobility: 6 (5.8%) - Avg Score: 33.3
      Career Silo: 6 (5.8%) - Avg Score: 9.8

   🚀 TOP MOBILITY SCORES:
      • Program & Project Delivery: Banking: 73.3 (Strong Launchpad)
        Components: Diversity=32.1, Destinations=30.0, Volume=5.0, Cross-boundary=6.2
      • Transformation: 72.6 (Strong Launchpad)
        Components: Diversity=35.6, Destinations=30.0, Volume=1.2, Cross-boundary=5.8
      • Relationship Management: 71.7 (Strong Launchpad)
        Components: Diversity=20.5, Destinations=30.0, Volume=20.0, Cross-boundary=1.3
      • Retail Banking Sales & Services: 71.4 (Strong Launchpad)
        Components: Diversity=19.9, Destinations=30.0, Volume=20.0, Cross-boundary=1.4
      • Business Services: 71.3 (Strong Launchpad)
        Components: Diversity=32.3, Destinations=30.0, Volume=6.1, Cross-boundary=3.0

   🔒 LOWEST MOBILITY SCORES:
      • Payroll: 13.5 (Career Silo)
      • Markets & Economic Research: 13.0 (Career Silo)
      • Property Management: 3.2 (Career Silo)
      • Executive: Private Bank: 3.1 (Career Silo)
      • Enterprise Architecture: 3.0 (Career Silo)
📊 Calculating enhanced movement probabilities for Job Sub-Function...
   → Calculated 1,737 enhanced movement probabilities

🔍 ANALYZING ARCHITECTURAL DIMENSION: Management Level
   → Analysis dataset: 27,312 complete records
   → Processing 8 Management Level values...
   📊 Mobility Score Summary for Management Level:
      Moderate Launchpad: 6 (75.0%) - Avg Score: 62.2
      Standard Mobility: 2 (25.0%) - Avg Score: 46.0

   🚀 TOP MOBILITY SCORES:
      • Group 3: 63.5 (Moderate Launchpad)
        Components: Diversity=24.1, Destinations=18.0, Volume=20.0, Cross-boundary=1.4
      • Group NA: 63.1 (Moderate Launchpad)
        Components: Diversity=20.4, Destinations=21.0, Volume=20.0, Cross-boundary=1.7
      • Group 4: 62.4 (Moderate Launchpad)
        Components: Diversity=19.5, Destinations=21.0, Volume=20.0, Cross-boundary=1.9
      • Group 2: 62.1 (Moderate Launchpad)
        Components: Diversity=25.4, Destinations=15.0, Volume=20.0, Cross-boundary=1.6
      • Group 5: 61.8 (Moderate Launchpad)
        Components: Diversity=21.2, Destinations=18.0, Volume=20.0, Cross-boundary=2.5

   🔒 LOWEST MOBILITY SCORES:
      • Group 2: 62.1 (Moderate Launchpad)
      • Group 5: 61.8 (Moderate Launchpad)
      • Group 1: 60.6 (Moderate Launchpad)
      • Group 7: 51.6 (Standard Mobility)
      • Group 6: 40.4 (Standard Mobility)
📊 Calculating enhanced movement probabilities for Management Level...
   → Calculated 42 enhanced movement probabilities

================================================================================
ENHANCED PATHWAY SCORING SYSTEM V2.0
================================================================================

📋 METHODOLOGY:
--------------------------------------------------

    Enhanced pathway scoring with architectural focus:
    1. Movement probability analysis (35% weight)
    2. Similarity score integration (25% weight)
    3. Mobility Score bonuses (20% weight)
    4. Skill match bonuses (10% weight)
    5. Architectural alignment scores (10% weight)



   📈 ENHANCED PATHWAY SCORING EXAMPLES FOR Job Profile:

      From R0262.11:
         → R0262.11:
           Total Score: 0.723
           Components: Similarity=0.175, Movement=0.231, Mobility=0.134, Skills=0.100
         → R0262.00:
           Total Score: 0.484
           Components: Similarity=0.175, Movement=0.020, Mobility=0.106, Skills=0.100
         → R0276.13:
           Total Score: 0.410
           Components: Similarity=0.175, Movement=0.017, Mobility=0.135, Skills=0.000

      From R0346.00:
         → R0346.00:
           Total Score: 0.771
           Components: Similarity=0.175, Movement=0.272, Mobility=0.126, Skills=0.100
         → R0347.00:
           Total Score: 0.433
           Components: Similarity=0.175, Movement=0.049, Mobility=0.112, Skills=0.000
         → R0349.00:
           Total Score: 0.413
           Components: Similarity=0.175, Movement=0.010, Mobility=0.131, Skills=0.000

      From R0033.15:
         → R0033.17:
           Total Score: 0.613
           Components: Similarity=0.175, Movement=0.125, Mobility=0.138, Skills=0.100
         → R0033.15:
           Total Score: 0.576
           Components: Similarity=0.175, Movement=0.080, Mobility=0.146, Skills=0.100
         → R0035.15:
           Total Score: 0.474
           Components: Similarity=0.175, Movement=0.033, Mobility=0.148, Skills=0.043

   📈 ENHANCED PATHWAY SCORING EXAMPLES FOR Job Sub-Function:

      From Retail Branch:
         → Retail Branch:
           Total Score: 0.660
           Components: Similarity=0.175, Movement=0.276, Mobility=0.125, Skills=0.000
         → Relationship Management:
           Total Score: 0.428
           Components: Similarity=0.175, Movement=0.025, Mobility=0.143, Skills=0.000
         → Retail Banking Sales &...:
           Total Score: 0.422
           Components: Similarity=0.175, Movement=0.019, Mobility=0.143, Skills=0.000

      From Business Banking:
         → Business Banking:
           Total Score: 0.639
           Components: Similarity=0.175, Movement=0.261, Mobility=0.129, Skills=0.000
         → Lending Operations:
           Total Score: 0.405
           Components: Similarity=0.175, Movement=0.019, Mobility=0.136, Skills=0.000
         → Relationship Management:
           Total Score: 0.408
           Components: Similarity=0.175, Movement=0.015, Mobility=0.143, Skills=0.000

      From Lending Operations:
         → Lending Operations:
           Total Score: 0.592
           Components: Similarity=0.175, Movement=0.213, Mobility=0.136, Skills=0.000
         → Business Banking:
           Total Score: 0.428
           Components: Similarity=0.175, Movement=0.056, Mobility=0.129, Skills=0.000
         → Credit Assessment:
           Total Score: 0.377
           Components: Similarity=0.175, Movement=0.012, Mobility=0.122, Skills=0.000

   📈 ENHANCED PATHWAY SCORING EXAMPLES FOR Management Level:

      From Group 3:
         → Group 3:
           Total Score: 0.573
           Components: Similarity=0.175, Movement=0.204, Mobility=0.127, Skills=0.000
         → Group 4:
           Total Score: 0.449
           Components: Similarity=0.175, Movement=0.082, Mobility=0.125, Skills=0.000
         → Group 2:
           Total Score: 0.413
           Components: Similarity=0.175, Movement=0.047, Mobility=0.124, Skills=0.000

      From Group 2:
         → Group 2:
           Total Score: 0.537
           Components: Similarity=0.175, Movement=0.172, Mobility=0.124, Skills=0.000
         → Group 3:
           Total Score: 0.501
           Components: Similarity=0.175, Movement=0.133, Mobility=0.127, Skills=0.000
         → Group 1:
           Total Score: 0.392
           Components: Similarity=0.175, Movement=0.030, Mobility=0.121, Skills=0.000

      From Group 1:
         → Group 1:
           Total Score: 0.598
           Components: Similarity=0.175, Movement=0.220, Mobility=0.121, Skills=0.000
         → Group 2:
           Total Score: 0.479
           Components: Similarity=0.175, Movement=0.098, Mobility=0.124, Skills=0.000
         → Group NA:
           Total Score: 0.408
           Components: Similarity=0.175, Movement=0.025, Mobility=0.126, Skills=0.000

================================================================================
ENHANCED ANALYSIS SUMMARY & STRATEGIC RECOMMENDATIONS V2.0
================================================================================
✅ ENHANCED MULTI-DIMENSIONAL ANALYSIS V2.0 COMPLETED
   → Analyzed 3 architectural dimensions
   → Processed 1171 total role classifications with Mobility Scores
   → Enterprise skills analysis: Completed
   → Created 3 enhanced scoring functions
💾 Memory Usage: 328.7 MB

🚀 V2.0 ENHANCEMENTS IMPLEMENTED:
   → Job Profile granularity (1,765 profiles vs 106 sub-functions)
   → Mobility Score gradient (0-100) replacing binary classification
   → Defining Skills feature with NAB enterprise rarity scoring
   → Architectural progression focus vs organizational context
   → Enhanced pathway scoring with skill matching and mobility bonuses
   → Temporal recency weighting with 40% decay rate for banking environment

🎯 KEY ENHANCED INSIGHTS:
   → Job Profile level provides actionable individual career guidance (1,765 profiles)
   → Mobility Scores reveal gradient of career progression potential
   → Defining Skills identify what makes each role unique at NAB (38,524 skills analyzed)
   → Architectural focus separates career progression from organizational placement
   → Enhanced scoring combines multiple factors for better pathway recommendations
   → Temporal weighting ensures recommendations reflect current career patterns

📊 STRATEGIC RECOMMENDATIONS V2.0:
   → Use Job Profile mobility scores for individual career counseling
   → Target defining skills development for role transitions
   → Focus on architectural progression patterns over organizational boundaries
   → Implement graduated mobility interventions based on score tiers
   → Leverage skill rarity insights for talent differentiation strategies
   → Apply recency weighting to prioritize recent career movement patterns

🔒 Database connection closed
💾 Memory Usage: 327.7 MB

================================================================================
ENHANCED ROLE TYPOLOGY & PATHWAY ENHANCEMENT ANALYSIS V2.0 COMPLETE
Total execution time: 15.00 seconds
================================================================================