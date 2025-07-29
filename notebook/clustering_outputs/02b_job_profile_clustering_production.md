PS C:\Users\P729965\OneDrive - nab\Documents\GitHub\skill-similarity-engine> python notebook/clustering/02b_job_profile_clustering_production.py
🚀 JOB PROFILE CLUSTERING - PRODUCTION 
=======================================

Target: 331 clusters with 0.962 silhouette score
================================================

✅ Connected to database: models/2025-Q3/workforce_intelligence.sqlite
📚 Loading comprehensive job-skill data...
   → Loaded columns: ['JobProfileID', 'Skill_ID', 'Skill_Name', 'Skill_Category', 'JobProfile', 'JobFunction', 'JobSubFunction', 'JobCategory', 'ManagementLevel']
   → Job-skill relationships: 76,994
   → Unique job profiles: 1,743
   → Unique skills: 2,442
🎯 Calculating defining skills (20% percentile strategy)...
   → Average defining skills per job: 9.7
   → Defining skills percentile: 20%
🔗 Creating enhanced similarity matrix with defining skills...
   → Calculating similarities for 1,743 job profiles...
   → Progress: 0/1743 (0.0%)
   → Progress: 100/1743 (5.7%)
   → Progress: 200/1743 (11.5%)
   → Progress: 300/1743 (17.2%)
   → Progress: 400/1743 (22.9%)
   → Progress: 500/1743 (28.7%)
   → Progress: 600/1743 (34.4%)
   → Progress: 700/1743 (40.2%)
   → Progress: 800/1743 (45.9%)
   → Progress: 900/1743 (51.6%)
   → Progress: 1000/1743 (57.4%)
   → Progress: 1100/1743 (63.1%)
   → Progress: 1200/1743 (68.8%)
   → Progress: 1300/1743 (74.6%)
   → Progress: 1400/1743 (80.3%)
   → Progress: 1500/1743 (86.1%)
   → Progress: 1600/1743 (91.8%)
   → Progress: 1700/1743 (97.5%)
   → Enhanced similarity matrix created: (1743, 1743)

🎯 PERFORMING PRODUCTION CLUSTERING
===================================

   → Using optimal parameters: eps=0.1, min_samples=2

✅ CLUSTERING RESULTS:
   → Clusters found: 320
   → Noise points: 84 (4.8%)
   → Silhouette score: 0.963
   → Expected clusters: 331
   → Expected silhouette: 0.962

📊 ANALYZING JOB CLUSTERS WITH DESCRIPTIVE NAMING
=================================================

   → Generating descriptive names for 320 clusters...
   → Generated descriptive names for all clusters
   → High confidence names: 248
   → Medium confidence names: 0
   → Low confidence names: 72

💾 SAVING CLUSTERING OUTPUTS WITH DESCRIPTIVE NAMES
===================================================

   → Primary output: job_clusters_production_20250727_164105.csv
   → Enhanced analysis report: job_cluster_analysis_20250727_164105.txt
   → Cluster details: job_cluster_characteristics_20250727_164105.csv
   → Naming analysis: job_cluster_naming_report_20250727_164105.txt

✅ All outputs saved with descriptive naming and timestamp: 20250727_164105

🎉 PRODUCTION CLUSTERING COMPLETED SUCCESSFULLY!
   → Generated 320 job clusters
   → Achieved 0.963 silhouette score
   → Ready for strategic workforce planning and pathway enhancement