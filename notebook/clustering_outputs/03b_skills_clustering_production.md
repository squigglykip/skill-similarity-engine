PS C:\Users\P729965\OneDrive - nab\Documents\GitHub\skill-similarity-engine> python notebook/clustering/03b_skills_clustering_production.py
🚀 SKILLS CLUSTERING - PRODUCTION 
==================================

Target: 193 skill bundles with 0.824 silhouette score
=====================================================

✅ Connected to database: models/2025-Q3/workforce_intelligence.sqlite
📚 Loading and filtering skills data...
   → Loaded columns: ['JobProfileID', 'Skill_ID', 'Skill_Name', 'Category', 'Subcategory', 'SkillType', 'JobFunction', 'JobSubFunction']
   → Raw job-skill relationships: 76,994
   → Raw unique skills: 2,442
   → After filtering:
     • Skills remaining: 2,205
     • Job-skill relationships: 76,648
     • Jobs covered: 1,743
   → Building skill co-occurrence matrix...
   → Co-occurrence matrix shape: (2205, 1743)
🔗 Creating cosine similarity matrix...
   → Cosine similarity matrix created: (2205, 2205)
   → Mean similarity: 0.013

🎯 PERFORMING PRODUCTION SKILLS CLUSTERING
==========================================

   → Using optimal parameters: cosine similarity, eps=0.1, min_samples=3

✅ CLUSTERING RESULTS:
   → Skill bundles found: 153
   → Specialized skills (noise): 1355 (61.5%)
   → Silhouette score: 0.947
   → Expected bundles: 193
   → Expected silhouette: 0.824
   → Expected noise ratio: 38.1%

📊 ANALYZING SKILL BUNDLES WITH DESCRIPTIVE NAMING
==================================================

   → Generating descriptive names for 153 skill bundles...
   → Analyzed 153 skill bundles
   → Bundles with ≥5 skills: 80
   → Specialized/emerging skills: 1355
🎯 Calculating taxonomy alignment...
   → Taxonomy alignment score: 0.604
   → Expected alignment: 0.563

📈 Creating skills clustering visualizations...
   📊 Plot saved: skills_clusters_production_overview_20250727_165521.png
   📊 Plot saved: skills_clusters_production_characteristics_20250727_165522.png

💾 SAVING SKILLS CLUSTERING OUTPUTS
===================================

   → Primary output: skills_clusters_production_20250727_165522.csv
   → Analysis report: skills_bundles_analysis_20250727_165522.txt
   → Specialized skills: specialized_emerging_skills_20250727_165522.csv
   → Bundle details: skill_bundles_characteristics_20250727_165522.csv
   → Learning pathways: learning_pathway_recommendations_20250727_165522.txt

✅ All skills clustering outputs saved with timestamp: 20250727_165522

🎉 PRODUCTION SKILLS CLUSTERING COMPLETED SUCCESSFULLY!
   → Generated 153 skill bundles
   → Achieved 0.947 silhouette score
   → Identified 1355 specialized/emerging skills
   → Taxonomy alignment: 0.604
   → Ready for L&D pathway design and skills taxonomy refinement