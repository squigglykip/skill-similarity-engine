PS C:\Users\P729965\OneDrive - nab\Documents\GitHub\skill-similarity-engine> python notebook/clustering/03a_skills_parameter_optimization.py
🎯 SKILLS CLUSTERING - PARAMETER OPTIMIZATION 
==============================================

🔍 Data-driven parameter selection for optimal skills clustering
📊 Comprehensive evaluation across similarity measures and algorithms

🎯 SKILLS CLUSTERING - PARAMETER OPTIMIZATION
=============================================

🔍 Systematic parameter testing for optimal skills clustering performance
📊 Testing multiple similarity measures and clustering algorithms
🏷️ Including taxonomy alignment validation

✅ Connected to database: models/2025-Q3/workforce_intelligence.sqlite
📚 Loading skills co-occurrence data for parameter optimization...
   → Total skills: 2,442
   → Filtered skills: 2,205
   → Job-skill relationships: 76,648
   → Building skill co-occurrence matrix...
   → Co-occurrence matrix shape: (2205, 2205)
🔗 Creating similarity matrices using different methods...
   → Calculating Jaccard similarity...
   → Calculating Cosine similarity...
   → Calculating Combined similarity...
   → Created 3 similarity matrices

🔍 OPTIMIZING DBSCAN PARAMETERS
===============================

   → Testing 315 parameter combinations...
   → Progress: 50/315 (15.9%)
   → Progress: 100/315 (31.7%)
   → Progress: 150/315 (47.6%)
   → Progress: 200/315 (63.5%)
   → Progress: 250/315 (79.4%)
   → Progress: 300/315 (95.2%)
   → Completed DBSCAN parameter optimization
   → Valid clustering results: 193/315

🔍 OPTIMIZING HIERARCHICAL CLUSTERING PARAMETERS
================================================

   → Testing 207 parameter combinations...
   → Progress: 25/207 (12.1%)
   → Progress: 50/207 (24.2%)
   → Progress: 75/207 (36.2%)
   → Progress: 100/207 (48.3%)
   → Progress: 125/207 (60.4%)
   → Progress: 150/207 (72.5%)
   → Progress: 175/207 (84.5%)
   → Progress: 200/207 (96.6%)
   → Completed hierarchical clustering optimization
   → Valid results: 207

🔍 OPTIMIZING K-MEANS PARAMETERS (ELBOW METHOD)
===============================================

   → jaccard: Reduced to 50 components
   → cosine: Reduced to 50 components
   → combined: Reduced to 50 components
   → Completed K-means optimization
   → Valid results: 69

🏆 FINDING OPTIMAL PARAMETERS
=============================

🥇 OPTIMAL DBSCAN PARAMETERS:
   → Similarity method: cosine
   → eps: 0.1
   → min_samples: 3
   → Expected clusters: 193
   → Expected noise ratio: 38.1%
   → Silhouette score: 0.824
   → Taxonomy alignment: 0.563

🥇 OPTIMAL HIERARCHICAL PARAMETERS:
   → Similarity method: combined
   → n_clusters: 8
   → linkage: average
   → Silhouette score: 0.064
   → Taxonomy alignment: 0.479

🥇 OPTIMAL K-MEANS PARAMETERS:
   → Similarity method: cosine
   → n_clusters: 8
   → Silhouette score: 0.175
   → Taxonomy alignment: 0.410

📈 Creating skills parameter optimization visualizations...
   📊 Plot saved: skills_param_opt_parameter_optimization_20250727_165007.png

💾 DBSCAN optimization results saved: skills_dbscan_optimization_20250727_165417.csv
💾 Hierarchical optimization results saved: skills_hierarchical_optimization_20250727_165417.csv
💾 K-means optimization results saved: skills_kmeans_optimization_20250727_165417.csv
💾 Parameter recommendations saved: skills_clustering_recommendations_20250727_165417.txt

🔒 Database connection closed

🎉 PARAMETER OPTIMIZATION COMPLETE!
📁 Check generated files and plots for optimal parameter recommendations
💡 Use recommended parameters in production clustering (03b file)