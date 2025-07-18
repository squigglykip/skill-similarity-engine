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
💾 Memory Usage: 188.9 MB

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
💾 Memory Usage: 393.2 MB
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
💾 Memory Usage: 314.6 MB

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

📖 SKILL RARITY DEFINITIONS:
• Prevalence Percentage: What % of NAB's job profiles require this skill
• Rarity Category: Classification based on enterprise-wide distribution
  - Rare (<5%): Highly specialised skills found in few roles
  - Uncommon (5-20%): Specialised skills with moderate distribution
  - Common (20-50%): Widely applicable skills across many roles
  - Universal (>50%): Core skills required by most positions
• Defining Skills: The 5 rarest skills that best characterise each job profile
• Rarity Score: Inverse measure of prevalence (higher = more distinctive/valuable)


✅ ENTERPRISE SKILL RARITY ANALYSIS COMPLETED
   → 2,442 skills analyzed across NAB enterprise
   → 1,743 job profiles with defining skill profiles

📊 SKILL RARITY DISTRIBUTION ACROSS NAB:
   • Rare: 2,272 skills (93.0%)
   • Uncommon: 140 skills (5.7%)
   • Common: 28 skills (1.1%)
   • Universal: 2 skills (0.1%)

🌉 SKILL MOBILITY ANALYSIS (Launchpads vs Silos):
🎯 Calculating skill mobility scores (launchpads vs silos)...
   → Loaded 528,714 movements and 76,994 job-skill mappings
   ⚠️  Skill mobility analysis failed: Unable to allocate 41.1 TiB for an array with shape (5650878500326,) and data type int64
   ⚠️  No skill mobility data available

🎯 DEFINING SKILLS EXAMPLES (What Makes These Roles Unique):

   📋 Executive Manager - 15:
      Skill Profile: 50 total skills, 35 rare/specialised
      Top Defining Skills (What Makes This Role Distinctive):
        1. Microsoft Access: 0.1% of roles (extremely rare)
        2. Predictive Statistics: 0.8% of roles (extremely rare)
        3. Managerial Finance: 1.1% of roles (highly specialised)

   📋 Executive Manager - 18:
      Skill Profile: 56 total skills, 26 rare/specialised
      Top Defining Skills (What Makes This Role Distinctive):
        1. Predictive Statistics: 0.8% of roles (extremely rare)
        2. Managerial Finance: 1.1% of roles (highly specialised)
        3. Predictive Modeling: 1.1% of roles (highly specialised)

   📋 Executive Manager - 19:
      Skill Profile: 50 total skills, 35 rare/specialised
      Top Defining Skills (What Makes This Role Distinctive):
        1. Microsoft Access: 0.1% of roles (extremely rare)
        2. Predictive Statistics: 0.8% of roles (extremely rare)
        3. Managerial Finance: 1.1% of roles (highly specialised)

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

📖 MOBILITY SCORE DEFINITIONS:
• Mobility Score (0-100): Overall career mobility potential combining multiple factors
• Diversity Component (0-40): Shannon diversity of transition destinations (higher = more varied career paths)
• Destinations Component (0-30): Number of unique destination roles (higher = more career options)
• Volume Component (0-20): Total movement frequency (higher = more active role transitions)
• Cross-boundary Component (0-10): Rate of moves across divisions/categories (higher = more boundary-crossing)

🏆 MOBILITY TIERS:
• Super Launchpad (85-100): Exceptional mobility with diverse, high-volume transitions
• Strong Launchpad (70-84): High mobility with multiple pathway options
• Moderate Launchpad (55-69): Good mobility with solid transition opportunities
• Standard Mobility (40-54): Average mobility following typical patterns
• Limited Mobility (25-39): Below-average mobility with fewer options
• Career Silo (0-24): Very limited mobility, concentrated in specific roles


   📊 MOBILITY SCORE DISTRIBUTION FOR JOB PROFILE:
      Standard Mobility: 339 roles (32.0%) - Average Score: 46.8
      Moderate Launchpad: 311 roles (29.3%) - Average Score: 62.4
      Career Silo: 278 roles (26.2%) - Average Score: 5.3
      Limited Mobility: 72 roles (6.8%) - Average Score: 34.3
      Unknown: 38 roles (3.6%) - Average Score: 54.9
      Strong Launchpad: 22 roles (2.1%) - Average Score: 71.1

   🚀 HIGHEST MOBILITY ROLES (Top Career Launchpads):
      • Business Banker: Small Business - 15
        Score: 74.1 (Strong Launchpad) - Ranks in top 0% of all roles
        Components: Diversity=22.8, Destinations=30.0, Volume=20.0, Cross-boundary=1.3
      • Business Banker: Middle Markets - 15
        Score: 73.1 (Strong Launchpad) - Ranks in top 0% of all roles
        Components: Diversity=22.7, Destinations=30.0, Volume=20.0, Cross-boundary=0.4
      • Personal Banker - 15
        Score: 72.4 (Strong Launchpad) - Ranks in top 0% of all roles
        Components: Diversity=35.5, Destinations=30.0, Volume=1.1, Cross-boundary=5.8
      • Administration Support - 00
        Score: 72.3 (Strong Launchpad) - Ranks in top 0% of all roles
        Components: Diversity=34.9, Destinations=30.0, Volume=0.8, Cross-boundary=6.7
      • Business Operations & Enablement - 20
        Score: 71.7 (Strong Launchpad) - Ranks in top 0% of all roles
        Components: Diversity=37.3, Destinations=30.0, Volume=0.5, Cross-boundary=3.9

   🔒 LOWEST MOBILITY ROLES (Career Development Focus Areas):
      • Marketing - 15
        Score: 3.0 (Career Silo) - Below median (bottom 8%)
      • R0237.12
        Score: 3.0 (Career Silo) - Below median (bottom 8%)
      • Business Continuity Planning - 18
        Score: 3.0 (Career Silo) - Below median (bottom 8%)
      • Systems Security Management - 13
        Score: 3.0 (Career Silo) - Below median (bottom 8%)
      • Transformation - 12
        Score: 3.0 (Career Silo) - Below median (bottom 8%)
📊 Calculating enhanced movement probabilities for Job Profile...
   → Calculated 5,491 enhanced movement probabilities

🔍 ANALYZING ARCHITECTURAL DIMENSION: Job Sub-Function
   → Analysis dataset: 27,312 complete records
   → Processing 103 Job Sub-Function values...

📖 MOBILITY SCORE DEFINITIONS:
• Mobility Score (0-100): Overall career mobility potential combining multiple factors
• Diversity Component (0-40): Shannon diversity of transition destinations (higher = more varied career paths)
• Destinations Component (0-30): Number of unique destination roles (higher = more career options)
• Volume Component (0-20): Total movement frequency (higher = more active role transitions)
• Cross-boundary Component (0-10): Rate of moves across divisions/categories (higher = more boundary-crossing)

🏆 MOBILITY TIERS:
• Super Launchpad (85-100): Exceptional mobility with diverse, high-volume transitions
• Strong Launchpad (70-84): High mobility with multiple pathway options
• Moderate Launchpad (55-69): Good mobility with solid transition opportunities
• Standard Mobility (40-54): Average mobility following typical patterns
• Limited Mobility (25-39): Below-average mobility with fewer options
• Career Silo (0-24): Very limited mobility, concentrated in specific roles


   📊 MOBILITY SCORE DISTRIBUTION FOR JOB SUB-FUNCTION:
      Moderate Launchpad: 52 roles (50.5%) - Average Score: 62.1
      Standard Mobility: 25 roles (24.3%) - Average Score: 47.3
      Strong Launchpad: 8 roles (7.8%) - Average Score: 71.5
      Unknown: 6 roles (5.8%) - Average Score: 56.8
      Limited Mobility: 6 roles (5.8%) - Average Score: 33.3
      Career Silo: 6 roles (5.8%) - Average Score: 9.8

   🚀 HIGHEST MOBILITY ROLES (Top Career Launchpads):
      • Program & Project Delivery: Banking
        Score: 73.3 (Strong Launchpad) - Ranks in top 0% of all roles
        Components: Diversity=32.1, Destinations=30.0, Volume=5.0, Cross-boundary=6.2
      • Transformation
        Score: 72.6 (Strong Launchpad) - Ranks in top 1% of all roles
        Components: Diversity=35.6, Destinations=30.0, Volume=1.2, Cross-boundary=5.8
      • Relationship Management
        Score: 71.7 (Strong Launchpad) - Ranks in top 2% of all roles
        Components: Diversity=20.5, Destinations=30.0, Volume=20.0, Cross-boundary=1.3
      • Retail Banking Sales & Services
        Score: 71.4 (Strong Launchpad) - Ranks in top 3% of all roles
        Components: Diversity=19.9, Destinations=30.0, Volume=20.0, Cross-boundary=1.4
      • Business Services
        Score: 71.3 (Strong Launchpad) - Ranks in top 4% of all roles
        Components: Diversity=32.3, Destinations=30.0, Volume=6.1, Cross-boundary=3.0

   🔒 LOWEST MOBILITY ROLES (Career Development Focus Areas):
      • Payroll
        Score: 13.5 (Career Silo) - Below median (bottom 5%)
      • Markets & Economic Research
        Score: 13.0 (Career Silo) - Below median (bottom 4%)
      • Property Management
        Score: 3.2 (Career Silo) - Below median (bottom 3%)
      • Executive: Private Bank
        Score: 3.1 (Career Silo) - Below median (bottom 2%)
      • Enterprise Architecture
        Score: 3.0 (Career Silo) - Below median (bottom 1%)
📊 Calculating enhanced movement probabilities for Job Sub-Function...
   → Calculated 1,737 enhanced movement probabilities

🔍 ANALYZING ARCHITECTURAL DIMENSION: Management Level
   → Analysis dataset: 27,312 complete records
   → Processing 8 Management Level values...

📖 MOBILITY SCORE DEFINITIONS:
• Mobility Score (0-100): Overall career mobility potential combining multiple factors
• Diversity Component (0-40): Shannon diversity of transition destinations (higher = more varied career paths)
• Destinations Component (0-30): Number of unique destination roles (higher = more career options)
• Volume Component (0-20): Total movement frequency (higher = more active role transitions)
• Cross-boundary Component (0-10): Rate of moves across divisions/categories (higher = more boundary-crossing)

🏆 MOBILITY TIERS:
• Super Launchpad (85-100): Exceptional mobility with diverse, high-volume transitions
• Strong Launchpad (70-84): High mobility with multiple pathway options
• Moderate Launchpad (55-69): Good mobility with solid transition opportunities
• Standard Mobility (40-54): Average mobility following typical patterns
• Limited Mobility (25-39): Below-average mobility with fewer options
• Career Silo (0-24): Very limited mobility, concentrated in specific roles


   📊 MOBILITY SCORE DISTRIBUTION FOR MANAGEMENT LEVEL:
      Moderate Launchpad: 6 roles (75.0%) - Average Score: 62.2
      Standard Mobility: 2 roles (25.0%) - Average Score: 46.0

   🚀 HIGHEST MOBILITY ROLES (Top Career Launchpads):
      • Group 3
        Score: 63.5 (Moderate Launchpad) - Ranks in top 0% of all roles
        Components: Diversity=24.1, Destinations=18.0, Volume=20.0, Cross-boundary=1.4
      • Group NA
        Score: 63.1 (Moderate Launchpad) - Ranks in top 12% of all roles
        Components: Diversity=20.4, Destinations=21.0, Volume=20.0, Cross-boundary=1.7
      • Group 4
        Score: 62.4 (Moderate Launchpad) - Ranks in top 25% of all roles
        Components: Diversity=19.5, Destinations=21.0, Volume=20.0, Cross-boundary=1.9
      • Group 2
        Score: 62.1 (Moderate Launchpad) - Ranks in top 38% of all roles
        Components: Diversity=25.4, Destinations=15.0, Volume=20.0, Cross-boundary=1.6
      • Group 5
        Score: 61.8 (Moderate Launchpad) - Below median (bottom 50%)
        Components: Diversity=21.2, Destinations=18.0, Volume=20.0, Cross-boundary=2.5

   🔒 LOWEST MOBILITY ROLES (Career Development Focus Areas):
      • Group 2
        Score: 62.1 (Moderate Launchpad) - Ranks in top 38% of all roles
      • Group 5
        Score: 61.8 (Moderate Launchpad) - Below median (bottom 50%)
      • Group 1
        Score: 60.6 (Moderate Launchpad) - Below median (bottom 38%)
      • Group 7
        Score: 51.6 (Standard Mobility) - Below median (bottom 25%)
      • Group 6
        Score: 40.4 (Standard Mobility) - Below median (bottom 12%)
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



📖 PATHWAY SCORING DEFINITIONS:
• Total Score (0-1): Combined pathway recommendation strength from all components
• Movement Component (35% weight): Historical probability of this specific transition occurring
• Similarity Component (25% weight): Role compatibility based on job architecture alignment
• Mobility Bonus (20% weight): Bonus for transitioning to high-mobility destination roles
• Skill Match Bonus (10% weight): Bonus for overlapping defining skills between roles
• Architectural Alignment (10% weight): Bonus for logical progression within job functions

💡 INTERPRETATION:
• Scores >0.7: Highly recommended pathways with strong historical precedent
• Scores 0.5-0.7: Good pathways with moderate support and opportunity
• Scores 0.3-0.5: Possible pathways requiring more development or networking
• Scores <0.3: Challenging pathways with limited historical precedent


   📈 PATHWAY SCORING EXAMPLES FOR JOB PROFILE:

      🎯 FROM: Banking Advisor - 11
         → TO: Banking Advisor - 11
           Score: 0.723 (🌟 Highly Recommended)
           Movement Probability: 0.231 | Similarity: 0.175 | Mobility Bonus: 0.134
           Historical Moves: 1824 people made this transition
         → TO: Banking Advisor - 00
           Score: 0.484 (⚠️ Possible (Development Needed))
           Movement Probability: 0.020 | Similarity: 0.175 | Mobility Bonus: 0.106
           Historical Moves: 158 people made this transition
         → TO: Home Lending - 13
           Score: 0.410 (⚠️ Possible (Development Needed))
           Movement Probability: 0.017 | Similarity: 0.175 | Mobility Bonus: 0.135
           Historical Moves: 136 people made this transition

      🎯 FROM: Quality Assurance: Automation - 00
         → TO: Quality Assurance: Automation - 00
           Score: 0.771 (🌟 Highly Recommended)
           Movement Probability: 0.272 | Similarity: 0.175 | Mobility Bonus: 0.126
           Historical Moves: 757 people made this transition
         → TO: Quality Assurance: Manual - 00
           Score: 0.433 (⚠️ Possible (Development Needed))
           Movement Probability: 0.049 | Similarity: 0.175 | Mobility Bonus: 0.112
           Historical Moves: 136 people made this transition
         → TO: Software Engineering - 00
           Score: 0.413 (⚠️ Possible (Development Needed))
           Movement Probability: 0.010 | Similarity: 0.175 | Mobility Bonus: 0.131
           Historical Moves: 28 people made this transition

      🎯 FROM: Business Banker: Middle Markets - 15
         → TO: Business Banker: Middle Markets - 17
           Score: 0.613 (✅ Good Pathway)
           Movement Probability: 0.125 | Similarity: 0.175 | Mobility Bonus: 0.138
           Historical Moves: 321 people made this transition
         → TO: Business Banker: Middle Markets - 15
           Score: 0.576 (✅ Good Pathway)
           Movement Probability: 0.080 | Similarity: 0.175 | Mobility Bonus: 0.146
           Historical Moves: 205 people made this transition
         → TO: Business Banker: Small Business - 15
           Score: 0.474 (⚠️ Possible (Development Needed))
           Movement Probability: 0.033 | Similarity: 0.175 | Mobility Bonus: 0.148
           Historical Moves: 85 people made this transition

📖 PATHWAY SCORING DEFINITIONS:
• Total Score (0-1): Combined pathway recommendation strength from all components
• Movement Component (35% weight): Historical probability of this specific transition occurring
• Similarity Component (25% weight): Role compatibility based on job architecture alignment
• Mobility Bonus (20% weight): Bonus for transitioning to high-mobility destination roles
• Skill Match Bonus (10% weight): Bonus for overlapping defining skills between roles
• Architectural Alignment (10% weight): Bonus for logical progression within job functions

💡 INTERPRETATION:
• Scores >0.7: Highly recommended pathways with strong historical precedent
• Scores 0.5-0.7: Good pathways with moderate support and opportunity
• Scores 0.3-0.5: Possible pathways requiring more development or networking
• Scores <0.3: Challenging pathways with limited historical precedent


   📈 PATHWAY SCORING EXAMPLES FOR JOB SUB-FUNCTION:

      🎯 FROM: Retail Branch
         → TO: Retail Branch
           Score: 0.660 (✅ Good Pathway)
           Movement Probability: 0.276 | Similarity: 0.175 | Mobility Bonus: 0.125
           Historical Moves: 3054 people made this transition
         → TO: Relationship Management
           Score: 0.428 (⚠️ Possible (Development Needed))
           Movement Probability: 0.025 | Similarity: 0.175 | Mobility Bonus: 0.143
           Historical Moves: 275 people made this transition
         → TO: Retail Banking Sales & Services
           Score: 0.422 (⚠️ Possible (Development Needed))
           Movement Probability: 0.019 | Similarity: 0.175 | Mobility Bonus: 0.143
           Historical Moves: 215 people made this transition

      🎯 FROM: Business Banking
         → TO: Business Banking
           Score: 0.639 (✅ Good Pathway)
           Movement Probability: 0.261 | Similarity: 0.175 | Mobility Bonus: 0.129
           Historical Moves: 2291 people made this transition
         → TO: Lending Operations
           Score: 0.405 (⚠️ Possible (Development Needed))
           Movement Probability: 0.019 | Similarity: 0.175 | Mobility Bonus: 0.136
           Historical Moves: 169 people made this transition
         → TO: Relationship Management
           Score: 0.408 (⚠️ Possible (Development Needed))
           Movement Probability: 0.015 | Similarity: 0.175 | Mobility Bonus: 0.143
           Historical Moves: 129 people made this transition

      🎯 FROM: Lending Operations
         → TO: Lending Operations
           Score: 0.592 (✅ Good Pathway)
           Movement Probability: 0.213 | Similarity: 0.175 | Mobility Bonus: 0.136
           Historical Moves: 1053 people made this transition
         → TO: Business Banking
           Score: 0.428 (⚠️ Possible (Development Needed))
           Movement Probability: 0.056 | Similarity: 0.175 | Mobility Bonus: 0.129
           Historical Moves: 278 people made this transition
         → TO: Credit Assessment
           Score: 0.377 (⚠️ Possible (Development Needed))
           Movement Probability: 0.012 | Similarity: 0.175 | Mobility Bonus: 0.122
           Historical Moves: 58 people made this transition

📖 PATHWAY SCORING DEFINITIONS:
• Total Score (0-1): Combined pathway recommendation strength from all components
• Movement Component (35% weight): Historical probability of this specific transition occurring
• Similarity Component (25% weight): Role compatibility based on job architecture alignment
• Mobility Bonus (20% weight): Bonus for transitioning to high-mobility destination roles
• Skill Match Bonus (10% weight): Bonus for overlapping defining skills between roles
• Architectural Alignment (10% weight): Bonus for logical progression within job functions

💡 INTERPRETATION:
• Scores >0.7: Highly recommended pathways with strong historical precedent
• Scores 0.5-0.7: Good pathways with moderate support and opportunity
• Scores 0.3-0.5: Possible pathways requiring more development or networking
• Scores <0.3: Challenging pathways with limited historical precedent


   📈 PATHWAY SCORING EXAMPLES FOR MANAGEMENT LEVEL:

      🎯 FROM: Group 3
         → TO: Group 3
           Score: 0.573 (✅ Good Pathway)
           Movement Probability: 0.204 | Similarity: 0.175 | Mobility Bonus: 0.127
           Historical Moves: 4458 people made this transition
         → TO: Group 4
           Score: 0.449 (⚠️ Possible (Development Needed))
           Movement Probability: 0.082 | Similarity: 0.175 | Mobility Bonus: 0.125
           Historical Moves: 1802 people made this transition
         → TO: Group 2
           Score: 0.413 (⚠️ Possible (Development Needed))
           Movement Probability: 0.047 | Similarity: 0.175 | Mobility Bonus: 0.124
           Historical Moves: 1023 people made this transition

      🎯 FROM: Group 2
         → TO: Group 2
           Score: 0.537 (✅ Good Pathway)
           Movement Probability: 0.172 | Similarity: 0.175 | Mobility Bonus: 0.124
           Historical Moves: 2878 people made this transition
         → TO: Group 3
           Score: 0.501 (✅ Good Pathway)
           Movement Probability: 0.133 | Similarity: 0.175 | Mobility Bonus: 0.127
           Historical Moves: 2221 people made this transition
         → TO: Group 1
           Score: 0.392 (⚠️ Possible (Development Needed))
           Movement Probability: 0.030 | Similarity: 0.175 | Mobility Bonus: 0.121
           Historical Moves: 505 people made this transition

      🎯 FROM: Group 1
         → TO: Group 1
           Score: 0.598 (✅ Good Pathway)
           Movement Probability: 0.220 | Similarity: 0.175 | Mobility Bonus: 0.121
           Historical Moves: 2793 people made this transition
         → TO: Group 2
           Score: 0.479 (⚠️ Possible (Development Needed))
           Movement Probability: 0.098 | Similarity: 0.175 | Mobility Bonus: 0.124
           Historical Moves: 1245 people made this transition
         → TO: Group NA
           Score: 0.408 (⚠️ Possible (Development Needed))
           Movement Probability: 0.025 | Similarity: 0.175 | Mobility Bonus: 0.126
           Historical Moves: 320 people made this transition

================================================================================
ENHANCED ANALYSIS SUMMARY & STRATEGIC RECOMMENDATIONS V2.0
================================================================================
✅ ENHANCED MULTI-DIMENSIONAL ANALYSIS V2.0 COMPLETED
   → Analyzed 3 architectural dimensions
   → Processed 1171 total role classifications with Mobility Scores
   → Enterprise skills analysis: Completed
   → Created 3 enhanced scoring functions
💾 Memory Usage: 332.1 MB

🚀 V2.0 ENHANCEMENTS IMPLEMENTED:
   → Job Profile granularity (1,765 profiles vs 106 sub-functions)
   → Mobility Score gradient (0-100) replacing binary classification
   → Defining Skills feature with NAB enterprise rarity scoring
   → Architectural progression focus vs organizational context
   → Enhanced pathway scoring with skill matching and mobility bonuses
   → Temporal recency weighting with 40% decay rate for banking environment

🎯 KEY ACTIONABLE INSIGHTS:
   → GRANULAR GUIDANCE: 1,765 job profiles with individual mobility scores
   → CAREER LAUNCHPADS: 22 roles identified as strong mobility platforms
   → DEVELOPMENT FOCUS: 278 roles requiring targeted career development support
   → SKILL INTELLIGENCE: 38,524 skills categorised by enterprise rarity
   → ARCHITECTURAL FOCUS: Career progression patterns separated from organisational placement
   → TEMPORAL RELEVANCE: Recent movement patterns weighted 60% higher than historical

📋 IMMEDIATE ACTIONABLE RECOMMENDATIONS:
   🎯 INDIVIDUAL CAREER COUNSELLING:
      • Use mobility scores (0-100) to set realistic progression expectations
      • Focus skill development on rare/defining skills for target roles
      • Prioritise pathways with scores >0.5 (good probability of success)
   🏢 ORGANISATIONAL TALENT STRATEGY:
      • Deploy high-mobility roles as talent development accelerators
      • Design intervention programs for Career Silo roles (score <25)
      • Leverage defining skills insights for targeted recruitment
   📊 MOBILITY TIER INTERVENTIONS:
      • Super/Strong Launchpads (70-100): Use as talent development hubs
      • Moderate Launchpads (55-69): Standard progression support
      • Limited Mobility/Silos (0-39): Enhanced development programs needed

🚀 TOP CAREER LAUNCHPAD ROLES TO LEVERAGE:
      1. Business Banker: Small Business - 15
      2. Business Banker: Middle Markets - 15
      3. Personal Banker - 15
      4. Administration Support - 00
      5. Business Operations & Enablement - 20

🔒 CAREER DEVELOPMENT PRIORITY ROLES:
      1. Risk Compliance - 15
      2. Financial Crime Operations - 18
      3. Cyber Crime Investigation - 20
      4. Portfolio Management - 20
      5. Settlements - 18

🔒 Database connection closed
💾 Memory Usage: 330.9 MB

================================================================================
ENHANCED ROLE TYPOLOGY & PATHWAY ENHANCEMENT ANALYSIS V2.0 COMPLETE
Total execution time: 44.29 seconds
================================================================================