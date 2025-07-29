PS C:\Users\P729965\OneDrive - nab\Documents\GitHub\skill-similarity-engine> python notebook/clustering/02a_job_profile_parameter_optimization.py
🎯 JOB PROFILE CLUSTERING - PARAMETER OPTIMIZATION 
===================================================

🔍 Data-driven parameter selection for optimal job clustering
📊 Comprehensive evaluation of DBSCAN and K-means parameters

🎯 JOB PROFILE CLUSTERING - PARAMETER OPTIMIZATION
==================================================

🔍 Systematic parameter testing for optimal clustering performance
📊 Using silhouette analysis, elbow method, and cluster stability metrics
⚙️ Enhanced similarity with 20% percentile, 1.05x multiplier

✅ Connected to database: models/2025-Q3/workforce_intelligence.sqlite
📚 Loading job profile and skill data...
   → Job profiles: 1,743
   → Total job-skill relationships: 76,994
   → Unique skills: 2,442
🎯 Creating job-specific defining skills (top 20% rarest per job)...
   → Average defining skills per job: 8.4
🔗 Creating enhanced job-to-job similarity matrix...
   → Calculating similarities for 1,743 job profiles...
   → Enhanced similarity matrix created

🔍 OPTIMIZING DBSCAN PARAMETERS
===============================

   → Testing 104 parameter combinations...
   → Progress: 20/104 (19.2%)
   → Progress: 40/104 (38.5%)
   → Progress: 60/104 (57.7%)
   → Progress: 80/104 (76.9%)
   → Progress: 100/104 (96.2%)
   → Completed parameter optimization
   → Valid clustering results: 104/104

🔍 OPTIMIZING K-MEANS PARAMETERS (ELBOW METHOD)
===============================================

   → Reduced dimensionality to 50 components
   → Explained variance ratio: 0.842
   → Features standardized for numerical stability
   → Testing 3 clusters (1/23)
   → Testing 4 clusters (2/23)
   → Testing 5 clusters (3/23)
   → Testing 6 clusters (4/23)
   → Testing 7 clusters (5/23)
   → Testing 8 clusters (6/23)
   → Testing 9 clusters (7/23)
   → Testing 10 clusters (8/23)
   → Testing 11 clusters (9/23)
   → Testing 12 clusters (10/23)
   → Testing 13 clusters (11/23)
   → Testing 14 clusters (12/23)
   → Testing 15 clusters (13/23)
   → Testing 16 clusters (14/23)
   → Testing 17 clusters (15/23)
   → Testing 18 clusters (16/23)
   → Testing 19 clusters (17/23)
   → Testing 20 clusters (18/23)
   → Testing 21 clusters (19/23)
   → Testing 22 clusters (20/23)
   → Testing 23 clusters (21/23)
   → Testing 24 clusters (22/23)
   → Testing 25 clusters (23/23)
   → Completed K-means optimization: 23/23 successful tests

🏆 FINDING OPTIMAL PARAMETERS
=============================

🥇 OPTIMAL DBSCAN PARAMETERS:
   → eps: 0.1
   → min_samples: 2.0
   → Expected clusters: 331.0
   → Expected noise ratio: 5.2%
   → Silhouette score: 0.962
   → Composite score: 0.921

🥇 OPTIMAL K-MEANS PARAMETERS:
   → Elbow method suggests: 23.0 clusters
   → Best silhouette score at: 25.0 clusters (0.181)
   → Recommended: 23.0 clusters

📈 Creating parameter optimization visualizations...
   📊 Plot saved: job_param_opt_parameter_optimization_20250727_163939.png

💾 DBSCAN optimization results saved: job_dbscan_optimization_20250727_163946.csv
💾 K-means optimization results saved: job_kmeans_optimization_20250727_163946.csv
💾 Parameter recommendations saved: job_clustering_recommendations_20250727_163946.txt

🔒 Database connection closed

🎉 PARAMETER OPTIMIZATION COMPLETE!
📁 Check generated files and plots for optimal parameter recommendations
💡 Use recommended parameters in production clustering (02b file)