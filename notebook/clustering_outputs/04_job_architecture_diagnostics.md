PS C:\Users\P729965\OneDrive - nab\Documents\GitHub\skill-similarity-engine> python notebook/clustering/04_job_architecture_diagnostics.py
🏥 JOB ARCHITECTURE & SKILLS TAXONOMY DIAGNOSTICS 
==================================================

📊 Comprehensive health evaluation with HR-friendly insights
🎯 Identifying taxonomic drift, redundancy, and governance opportunities

🏥 JOB ARCHITECTURE & SKILLS TAXONOMY HEALTH DIAGNOSTICS
========================================================

📊 Comprehensive evaluation of organizational job architecture health
🎯 Focus: Actionable insights for HR stakeholders and governance

✅ Connected to database: models/2025-Q3/workforce_intelligence.sqlite
📚 Loading diagnostic data...
   → Job profiles: 1,743
   → Job-skill relationships: 76,994
   → Unique skills: 2,442
   → Job functions: 27

============================================================
🎯 SILHOUETTE SCORE ANALYSIS
============================

📊 Measuring functional cohesion and separation between job profiles
🔗 Creating job-skill matrix...
   → Matrix shape: (1743, 2442)
   → Sparsity: 98.2%
   → Calculating job similarity matrix...

📈 OVERALL TAXONOMIC HEALTH:
   → Overall Silhouette Score: 0.047
   → HR Translation: These roles are not clearly different from others - potential redesign needed
   → Recommendation: This unit's structure may not reflect skill reality – discussion warranted
   🔴 ATTENTION NEEDED: Significant role overlap requiring strategic review

🏢 BUSINESS UNIT ANALYSIS:
   → Analyzing 27 business units/functions

   Top Performing Units (Clear Role Differentiation):
   🟡 Business Bank: 0.653 avg (24 roles)
      → These roles have moderate clarity but may benefit from review
   🔴 Strategy & Innovation: 0.394 avg (16 roles)
      → These roles are not clearly different from others - potential redesign needed
   🔴 Procurement: 0.336 avg (23 roles)
      → These roles are not clearly different from others - potential redesign needed
   🔴 Business Development Management: 0.212 avg (14 roles)
      → These roles are not clearly different from others - potential redesign needed
   🔴 Private Bank: 0.180 avg (19 roles)
      → These roles are not clearly different from others - potential redesign needed

   Units Needing Attention (Poor Role Differentiation):
   🔴 Executive Leadership: -0.005 avg (127 roles)
      → 127 roles with poor differentiation
      → These roles/families need targeted review or redesign
   🔴 Technology Enablement & Operations: -0.008 avg (191 roles)
      → 191 roles with poor differentiation
      → These roles/families need targeted review or redesign
   🔴 Risk: -0.010 avg (161 roles)
      → 161 roles with poor differentiation
      → These roles/families need targeted review or redesign
   🔴 Markets & Institutional Bank: -0.032 avg (185 roles)
      → 185 roles with poor differentiation
      → These roles/families need targeted review or redesign
   🔴 Fulfilment & Operations: -0.040 avg (144 roles)
      → 144 roles with poor differentiation
      → These roles/families need targeted review or redesign

⚠️  INDIVIDUAL ROLE ALERTS:
   → 1680 roles with poor differentiation (silhouette < 0.3)

   Most Problematic Roles (requiring immediate review):
   🔴 Transaction Banking: Account Manager - 18 (Markets & Institutional Bank)
      → Silhouette: -0.193
      → Issue: Role not clearly differentiated from others in skill requirements
   🔴 Transaction Banking: Sales - 18 (Markets & Institutional Bank)
      → Silhouette: -0.189
      → Issue: Role not clearly differentiated from others in skill requirements
   🔴 Database Administrator - 16 (Technology Enablement & Operations)
      → Silhouette: -0.186
      → Issue: Role not clearly differentiated from others in skill requirements
   🔴 Markets Quantitative Analyst - 20 (Markets & Institutional Bank)
      → Silhouette: -0.184
      → Issue: Role not clearly differentiated from others in skill requirements
   🔴 Trading: Derivatives & Swaps - 20 (Markets & Institutional Bank)
      → Silhouette: -0.184
      → Issue: Role not clearly differentiated from others in skill requirements
   🔴 Transaction Banking: Sales - 20 (Markets & Institutional Bank)
      → Silhouette: -0.183
      → Issue: Role not clearly differentiated from others in skill requirements
   🔴 Sales: Bullion & Commodities - 20 (Markets & Institutional Bank)
      → Silhouette: -0.182
      → Issue: Role not clearly differentiated from others in skill requirements
   🔴 Transaction Banking: Account Manager - 20 (Markets & Institutional Bank)
      → Silhouette: -0.181
      → Issue: Role not clearly differentiated from others in skill requirements
   🔴 Trading: Fixed Income & Equities - 20 (Markets & Institutional Bank)
      → Silhouette: -0.180
      → Issue: Role not clearly differentiated from others in skill requirements
   🔴 Trade & Working Capital Finance - 14 (Markets & Institutional Bank)
      → Silhouette: -0.173
      → Issue: Role not clearly differentiated from others in skill requirements

============================================================
🔍 SKILL SIMILARITY ANALYSIS
============================

📊 Detecting role redundancy and excessive standardization
🔗 Creating job-skill matrix...
   → Matrix shape: (1743, 2442)
   → Sparsity: 98.2%
   → Calculating pairwise job similarities...

📊 SIMILARITY ANALYSIS RESULTS:
   → Analyzed 1,518,153 job pairs
   → Average Jaccard similarity: 0.072
   → Average Cosine similarity: 0.122

🔍 NEAR-DUPLICATE ROLE DETECTION:
   🔴 ALERT: 2619 role pairs with high skill overlap (Jaccard > 0.85)
   HR Translation: These roles are almost identical—do we need both?

   Most Similar Role Pairs:
   • Executive Manager - 15 ↔ Executive Manager - 19
     Functions: Administrative & Business Services | Administrative & Business Services
     Similarity: 1.000
   • Executive Manager - 18 ↔ Executive Manager - 20
     Functions: Administrative & Business Services | Administrative & Business Services
     Similarity: 1.000
   • Administration Support - 00 ↔ Administration Support - 11
     Functions: Administrative & Business Services | Administrative & Business Services
     Similarity: 1.000
   • Administration Support - 00 ↔ Administration Support - 12
     Functions: Administrative & Business Services | Administrative & Business Services
     Similarity: 1.000
   • Administration Support - 00 ↔ Administration Support - 13
     Functions: Administrative & Business Services | Administrative & Business Services
     Similarity: 1.000
   • Administration Support - 00 ↔ Administration Support - 15
     Functions: Administrative & Business Services | Administrative & Business Services
     Similarity: 1.000
   • Administration Support - 00 ↔ Administration Support - 17
     Functions: Administrative & Business Services | Administrative & Business Services
     Similarity: 1.000
   • Administration Support - 00 ↔ Administration Support - 19
     Functions: Administrative & Business Services | Administrative & Business Services
     Similarity: 1.000
   • Administration Support - 11 ↔ Administration Support - 12
     Functions: Administrative & Business Services | Administrative & Business Services
     Similarity: 1.000
   • Administration Support - 11 ↔ Administration Support - 13
     Functions: Administrative & Business Services | Administrative & Business Services
     Similarity: 1.000

   🔴 SEMANTIC REDUNDANCY: 2692 pairs with high semantic similarity
   → These roles may have conceptual overlap requiring clarification

📈 ROLE FAMILY HOMOGENEITY ANALYSIS:
   🔴 ALERT: 25 functions with low internal variance
   HR Translation: These job families may be too homogenous—limited role clarity
   • Administrative & Business Services: 0.068 variance (60 roles)
     → Consider adding role differentiation or combining similar positions
   • Business Bank: 0.015 variance (24 roles)
     → Consider adding role differentiation or combining similar positions
   • Asset & Portfolio Management: 0.075 variance (39 roles)
     → Consider adding role differentiation or combining similar positions
   • Executive Leadership: 0.007 variance (127 roles)
     → Consider adding role differentiation or combining similar positions
   • Private Bank: 0.069 variance (19 roles)
     → Consider adding role differentiation or combining similar positions
   • Regulatory & Compliance: 0.062 variance (55 roles)
     → Consider adding role differentiation or combining similar positions
   • Customer Resolution & Remediation: 0.042 variance (59 roles)
     → Consider adding role differentiation or combining similar positions
   • Business Development Management: 0.082 variance (14 roles)
     → Consider adding role differentiation or combining similar positions
   • Marketing & Communications: 0.050 variance (61 roles)
     → Consider adding role differentiation or combining similar positions
   • Data & Analytics: 0.070 variance (63 roles)
     → Consider adding role differentiation or combining similar positions
   • Technology Enablement & Operations: 0.044 variance (191 roles)
     → Consider adding role differentiation or combining similar positions
   • Risk: 0.041 variance (161 roles)
     → Consider adding role differentiation or combining similar positions
   • Markets & Institutional Bank: 0.025 variance (185 roles)
     → Consider adding role differentiation or combining similar positions
   • Group Executive & Directors: 0.003 variance (9 roles)
     → Consider adding role differentiation or combining similar positions
   • Finance & Accounting: 0.061 variance (71 roles)
     → Consider adding role differentiation or combining similar positions
   • Fulfilment & Operations: 0.048 variance (144 roles)
     → Consider adding role differentiation or combining similar positions
   • Product & Digital Experience: 0.068 variance (62 roles)
     → Consider adding role differentiation or combining similar positions
   • People & Culture: 0.053 variance (89 roles)
     → Consider adding role differentiation or combining similar positions
   • Procurement: 0.083 variance (23 roles)
     → Consider adding role differentiation or combining similar positions
   • Program Management: 0.042 variance (46 roles)
     → Consider adding role differentiation or combining similar positions
   • Agile: 0.078 variance (33 roles)
     → Consider adding role differentiation or combining similar positions
   • Business Transformation: 0.076 variance (50 roles)
     → Consider adding role differentiation or combining similar positions
   • Technology Architecture: 0.086 variance (26 roles)
     → Consider adding role differentiation or combining similar positions
   • Retail Bank: 0.077 variance (41 roles)
     → Consider adding role differentiation or combining similar positions
   • Technology Development & Engineering: 0.074 variance (50 roles)
     → Consider adding role differentiation or combining similar positions

============================================================
🕸️  GRAPH-BASED STRUCTURAL ANALYSIS
=====================================

📊 Community detection and network analysis of job-skill relationships
   → Building bipartite job-skill graph...
   → Graph created: 4,185 nodes, 76,994 edges
   → Calculating skill centrality measures...
   → Performing community detection on job network...

🎯 NETWORK STRUCTURE INSIGHTS:
   → Network density: 0.3541
   → Connected components: 1
   → Average clustering coefficient: 0.696

🌟 HUB SKILLS ANALYSIS:
   🟢 No skills identified as being overused across unrelated functions

🏘️  COMMUNITY STRUCTURE ANALYSIS:
   → Detected 5 natural job communities
   HR Translation: These roles naturally group together—they may form coherent job families

   🟢 Strong Natural Families (align well with current structure):
   • Community 4: 19 roles
     → 100.0% Product & Digital Experience
     → Interpretation: Well-defined job family with clear boundaries
   • Community 3: 65 roles
     → 100.0% Technology Enablement & Operations
     → Interpretation: Well-defined job family with clear boundaries

   🟡 Cross-Functional Communities (potential new job families):
   • Community 0: 443 roles
     → Mixed functions: Administrative & Business Services (39), Regulatory & Compliance (39), Marketing & Communications (39)
     → Interpretation: Skills-based grouping that transcends current boundaries
   • Community 1: 597 roles
     → Mixed functions: Administrative & Business Services (12), Business Bank (6), Asset & Portfolio Management (😎
     → Interpretation: Skills-based grouping that transcends current boundaries
   • Community 2: 619 roles
     → Mixed functions: Business Bank (18), Asset & Portfolio Management (31), Executive Leadership (24)
     → Interpretation: Skills-based grouping that transcends current boundaries

============================================================
🌈 ENTROPY & DIVERSITY ANALYSIS
===============================

📊 Measuring role focus vs generality and business unit skill diversity
   → Calculating skill entropy per job...
   → Analyzing skill diversity per business unit...

📊 JOB ROLE FOCUS ANALYSIS:
   → Average job entropy: 2.42
   → Jobs analyzed: 1743

   🟡 HIGHLY SPECIALIZED ROLES (low entropy < 1.5):
   • User Interface Design - 15 (Product & Digital Experience)
     → Entropy: 0.64, 17 skills in 3 categories
     → Note: High specialization may be appropriate for technical roles
   • Orchestration - 17 (Agile)
     → Entropy: 0.66, 44 skills in 3 categories
     → Note: High specialization may be appropriate for technical roles
   • Orchestration - 19 (Agile)
     → Entropy: 0.66, 44 skills in 3 categories
     → Note: High specialization may be appropriate for technical roles
   • Program Delivery: Corporate - 13 (Program Management)
     → Entropy: 0.78, 43 skills in 3 categories
     → Note: High specialization may be appropriate for technical roles
   • Program Delivery: Corporate - 15 (Program Management)
     → Entropy: 0.78, 43 skills in 3 categories
     → Note: High specialization may be appropriate for technical roles

🏢 BUSINESS UNIT SKILL DIVERSITY:
   → Analyzed 27 business units

   🔴 LOW SKILL DIVERSITY (potential risk of inflexibility):
   HR Translation: These units may be too skill-narrow—risk of inflexibility
   • Administrative & Business Services: 5.0 skills per job
     → 301 unique skills across 60 roles
     → Recommendation: Consider cross-training and skill diversification
   • Business Bank: 3.8 skills per job
     → 91 unique skills across 24 roles
     → Recommendation: Consider cross-training and skill diversification
   • Asset & Portfolio Management: 4.0 skills per job
     → 156 unique skills across 39 roles
     → Recommendation: Consider cross-training and skill diversification
   • Executive Leadership: 7.2 skills per job
     → 913 unique skills across 127 roles
     → Recommendation: Consider cross-training and skill diversification
   • Private Bank: 6.8 skills per job
     → 130 unique skills across 19 roles
     → Recommendation: Consider cross-training and skill diversification
   • Regulatory & Compliance: 4.5 skills per job
     → 245 unique skills across 55 roles
     → Recommendation: Consider cross-training and skill diversification
   • Customer Resolution & Remediation: 2.4 skills per job
     → 140 unique skills across 59 roles
     → Recommendation: Consider cross-training and skill diversification
   • Business Development Management: 9.3 skills per job
     → 130 unique skills across 14 roles
     → Recommendation: Consider cross-training and skill diversification
   • Marketing & Communications: 3.9 skills per job
     → 236 unique skills across 61 roles
     → Recommendation: Consider cross-training and skill diversification
   • Data & Analytics: 4.0 skills per job
     → 252 unique skills across 63 roles
     → Recommendation: Consider cross-training and skill diversification
   • Technology Enablement & Operations: 3.0 skills per job
     → 568 unique skills across 191 roles
     → Recommendation: Consider cross-training and skill diversification
   • Risk: 2.1 skills per job
     → 336 unique skills across 161 roles
     → Recommendation: Consider cross-training and skill diversification
   • Markets & Institutional Bank: 3.5 skills per job
     → 650 unique skills across 185 roles
     → Recommendation: Consider cross-training and skill diversification
   • Finance & Accounting: 3.3 skills per job
     → 236 unique skills across 71 roles
     → Recommendation: Consider cross-training and skill diversification
   • Fulfilment & Operations: 2.2 skills per job
     → 320 unique skills across 144 roles
     → Recommendation: Consider cross-training and skill diversification
   • Product & Digital Experience: 4.9 skills per job
     → 302 unique skills across 62 roles
     → Recommendation: Consider cross-training and skill diversification
   • People & Culture: 3.6 skills per job
     → 318 unique skills across 89 roles
     → Recommendation: Consider cross-training and skill diversification
   • Procurement: 3.5 skills per job
     → 81 unique skills across 23 roles
     → Recommendation: Consider cross-training and skill diversification
   • Program Management: 3.9 skills per job
     → 178 unique skills across 46 roles
     → Recommendation: Consider cross-training and skill diversification
   • Agile: 4.4 skills per job
     → 145 unique skills across 33 roles
     → Recommendation: Consider cross-training and skill diversification
   • Business Transformation: 3.3 skills per job
     → 167 unique skills across 50 roles
     → Recommendation: Consider cross-training and skill diversification
   • Technology Architecture: 7.3 skills per job
     → 191 unique skills across 26 roles
     → Recommendation: Consider cross-training and skill diversification
   • Retail Bank: 4.0 skills per job
     → 164 unique skills across 41 roles
     → Recommendation: Consider cross-training and skill diversification
   • Strategy & Innovation: 5.9 skills per job
     → 95 unique skills across 16 roles
     → Recommendation: Consider cross-training and skill diversification
   • Technology Development & Engineering: 3.9 skills per job
     → 196 unique skills across 50 roles
     → Recommendation: Consider cross-training and skill diversification
   • Property & Facilities Management: 5.7 skills per job
     → 143 unique skills across 25 roles
     → Recommendation: Consider cross-training and skill diversification

======================================================================
📋 EXECUTIVE SUMMARY & GOVERNANCE RECOMMENDATIONS
=================================================

🎯 OVERALL ARCHITECTURE HEALTH: ATTENTION NEEDED
   🔴 REQUIRES ATTENTION: Significant structural issues identified
   → These roles/families need targeted review or redesign

🔴 MAJOR ISSUES REQUIRING IMMEDIATE ATTENTION:
   • Poor functional differentiation across roles
   • 2619 near-duplicate role pairs

📊 KEY PERFORMANCE INDICATORS (for ongoing monitoring):
   → % of roles with poor differentiation: 96.4%
     Target: <5% | Current Status: 🔴
   → Overall silhouette score: 0.047
     Target: >0.4 | Current Status: 🔴
   → % roles in near-duplicate pairs: 150.3%
     Target: <2% | Current Status: 🔴
   → Number of overused skills: 0
     Target: <10 | Current Status: 🟢

📅 RECOMMENDED REPORTING CADENCE:
   → Monthly light-touch dashboard: Silhouette score, duplicate count, role changes
   → Quarterly in-depth audit: Full diagnostic analysis with trend analysis
   → Post-update validation: Run diagnostics after any job architecture changes

🎯 NEXT STEPS:

1. Address any major issues identified above
2. Set up automated monitoring for key metrics
3. Establish quarterly review process with stakeholders
4. Create intervention protocols for metric thresholds

🔒 Database connection closed

🎉 DIAGNOSTIC ANALYSIS COMPLETE!
📋 Use insights above for strategic workforce planning and governance
🔄 Recommend establishing regular diagnostic monitoring for ongoing health