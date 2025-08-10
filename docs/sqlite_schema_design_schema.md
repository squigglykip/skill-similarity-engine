# Database Schema Documentation

**Generated for LLM Consumption**

## Database Overview

- **Database Size**: 363.35 MB
- **SQLite Version**: 3.45.3
- **Last Modified**: 2025-08-10
- **Total Tables**: 16
- **Total Records**: 670,590

## Table of Contents

### analytics
- [analytics_bundle_characteristics](#analytics-bundle-characteristics)
- [analytics_job_defining_skills](#analytics-job-defining-skills)
- [analytics_job_families](#analytics-job-families)
- [analytics_job_family_characteristics](#analytics-job-family-characteristics)
- [analytics_job_similarities](#analytics-job-similarities)
- [analytics_movement_patterns](#analytics-movement-patterns)
- [analytics_pathway_predictions](#analytics-pathway-predictions)
- [analytics_skill_bundles](#analytics-skill-bundles)
- [analytics_skill_demand_trends](#analytics-skill-demand-trends)
- [analytics_skill_rarity](#analytics-skill-rarity)
- [analytics_specialized_skills](#analytics-specialized-skills)

### core
- [core_job_architecture](#core-job-architecture)
- [core_job_skill_requirements](#core-job-skill-requirements)
- [core_skills_taxonomy](#core-skills-taxonomy)
- [core_workforce_current](#core-workforce-current)

### system
- [sys_schema_metadata](#sys-schema-metadata)

---

## Database Relationships Overview

### Key Foreign Key Relationships

- `analytics_bundle_characteristics.cluster_id` → `analytics_skill_bundles.cluster_id`
- `analytics_job_defining_skills.skill_id` → `core_skills_taxonomy.Skill_ID`
- `analytics_job_defining_skills.job_profile_id` → `core_job_architecture.JobProfileID`
- `analytics_job_families.job_profile_id` → `core_job_architecture.JobProfileID`
- `analytics_job_family_characteristics.cluster_id` → `analytics_job_families.cluster_id`
- `analytics_job_similarities.job_to` → `core_job_architecture.JobProfileID`
- `analytics_job_similarities.job_from` → `core_job_architecture.JobProfileID`
- `analytics_movement_patterns.to_job_profile_id` → `core_job_architecture.JobProfileID`
- `analytics_movement_patterns.from_job_profile_id` → `core_job_architecture.JobProfileID`
- `analytics_pathway_predictions.to_job_profile_id` → `core_job_architecture.JobProfileID`
- `analytics_pathway_predictions.from_job_profile_id` → `core_job_architecture.JobProfileID`
- `analytics_skill_bundles.skill_id` → `core_skills_taxonomy.Skill_ID`
- `analytics_skill_demand_trends.skill_id` → `core_skills_taxonomy.Skill_ID`
- `analytics_skill_rarity.skill_id` → `core_skills_taxonomy.Skill_ID`
- `analytics_specialized_skills.skill_id` → `core_skills_taxonomy.Skill_ID`
- `core_job_skill_requirements.Skill_ID` → `core_skills_taxonomy.Skill_ID`
- `core_job_skill_requirements.JobProfileID` → `core_job_architecture.JobProfileID`
- `core_workforce_current.JobProfileID` → `core_job_architecture.JobProfileID`

---

## Detailed Table Specifications

## analytics Tables

### analytics_bundle_characteristics

**Records**: 27

#### Schema

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `cluster_id` | INTEGER | PK, FK | Cluster Id |
| `bundle_name` | TEXT | - | Bundle Name |
| `bundle_description` | TEXT | - | Bundle Description |
| `bundle_rationale` | TEXT | - | Bundle Rationale |
| `bundle_size` | INTEGER | - | Bundle Size |
| `sample_skills` | TEXT | - | Sample Skills |
| `sample_job_functions` | TEXT | - | Sample Job Functions |
| `core_skills` | TEXT | - | Core Skills |
| `peripheral_skills` | TEXT | - | Peripheral Skills |
| `dominant_category` | TEXT | - | Dominant Category |
| `category_purity` | REAL | - | Category Purity |
| `application_level` | TEXT | - | Application Level |
| `specialization_area` | TEXT | - | Specialization Area |
| `average_jobs_per_skill` | REAL | - | Average Jobs Per Skill |
| `taxonomy_alignment_score` | REAL | - | Taxonomy Alignment Score |
| `silhouette_score` | REAL | - | Silhouette Score |
| `intra_bundle_cohesion` | REAL | - | Intra Bundle Cohesion |
| `inter_bundle_separation` | REAL | - | Inter Bundle Separation |
| `business_value_score` | REAL | - | Business Value Score |
| `training_feasibility` | TEXT | - | Training Feasibility |
| `skill_complementarity` | REAL | - | Skill Complementarity |
| `market_demand_level` | TEXT | - | Market Demand Level |
| `common_job_families` | TEXT | - | Common Job Families |
| `typical_career_stage` | TEXT | - | Typical Career Stage |
| `skill_acquisition_difficulty` | TEXT | - | Skill Acquisition Difficulty |
| `clustering_algorithm` | TEXT | - | Clustering Algorithm |
| `algorithm_parameters` | TEXT | - | Algorithm Parameters |
| `quality_validation_date` | TEXT | - | Quality Validation Date |
| `business_review_date` | TEXT | - | Business Review Date |
| `created_timestamp` | TEXT | - | Created Timestamp |

#### Foreign Key Relationships

- `cluster_id` references `analytics_skill_bundles.cluster_id`

#### Sample Data

```json
{
  "cluster_id": 0,
  "bundle_name": "Analysis Skills Bundle (91 skills)",
  "bundle_description": "Collection of Analysis skills with 3.1% average prevalence",
  "bundle_rationale": "Grouped by Analysis category",
  "bundle_size": 91,
  "sample_skills": "Customer Centricity; Data Analysis; Data Literacy",
  "sample_job_functions": "Analysis pending",
  "core_skills": null,
  "peripheral_skills": null,
  "dominant_category": "Analysis",
  "category_purity": 1.0,
  "application_level": "Advanced",
  "specialization_area": "Analysis",
  "average_jobs_per_skill": 22.428571428571427,
  "taxonomy_alignment_score": 0.8,
  "silhouette_score": 0.0,
  "intra_bundle_cohesion": null,
  "inter_bundle_separation": null,
  "business_value_score": null,
  "training_feasibility": null,
  "skill_complementarity": null,
  "market_demand_level": null,
  "common_job_families": null,
  "typical_career_stage": null,
  "skill_acquisition_difficulty": null,
  "clustering_algorithm": null,
  "algorithm_parameters": null,
  "quality_validation_date": null,
  "business_review_date": null,
  "created_timestamp": "2025-08-10T19:19:10.988391"
}
```

*(5 sample records available)*

---

### analytics_job_defining_skills

**Records**: 19,460

#### Schema

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `job_profile_id` | TEXT | PK, FK | Job Profile Id |
| `skill_id` | TEXT | PK, FK | Skill Id |
| `skill_name` | TEXT | - | Skill Name |
| `job_profile` | TEXT | - | Job Profile |
| `category` | TEXT | - | Category |
| `subcategory` | TEXT | - | Subcategory |
| `skill_type` | TEXT | - | Skill Type |
| `prevalence_percentage` | REAL | - | Prevalence Percentage |
| `total_profiles_with_skill` | INTEGER | - | Total Profiles With Skill |
| `rarity_category` | TEXT | - | Rarity Category |
| `defining_skill_rank` | INTEGER | - | Defining Skill Rank |
| `defining_skill_score` | REAL | - | Defining Skill Score |
| `analysis_date` | TEXT | - | Analysis Date |
| `percentile_threshold` | REAL | - | Percentile Threshold |
| `created_timestamp` | TEXT | - | Created Timestamp |

#### Foreign Key Relationships

- `skill_id` references `core_skills_taxonomy.Skill_ID`
- `job_profile_id` references `core_job_architecture.JobProfileID`

#### Sample Data

```json
{
  "job_profile_id": "R0001.5",
  "skill_id": "KS122CJ6ZVCCTTDGYB6B",
  "skill_name": "Contract Negotiation",
  "job_profile": "Payment Systems Analyst - 5",
  "category": "Business",
  "subcategory": "Contract Management",
  "skill_type": "Specialized Skill",
  "prevalence_percentage": 1.4,
  "total_profiles_with_skill": 10,
  "rarity_category": "Rare",
  "defining_skill_rank": 6,
  "defining_skill_score": 98.6013986013986,
  "analysis_date": "2025-08-10",
  "percentile_threshold": 8.8,
  "created_timestamp": "2025-08-10 09:15:08"
}
```

*(5 sample records available)*

---

### analytics_job_families

**Records**: 715

#### Schema

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `job_profile_id` | TEXT | PK, FK | Job Profile Id |
| `job_profile` | TEXT | - | Job Profile |
| `job_function` | TEXT | - | Job Function |
| `job_sub_function` | TEXT | - | Job Sub Function |
| `job_category` | TEXT | - | Job Category |
| `management_level` | TEXT | - | Management Level |
| `cluster_id` | INTEGER | PK | Cluster Id |
| `cluster_name` | TEXT | - | Cluster Name |
| `cluster_description` | TEXT | - | Cluster Description |
| `cluster_rationale` | TEXT | - | Cluster Rationale |
| `cluster_size` | INTEGER | - | Cluster Size |
| `sample_jobs` | TEXT | - | Sample Jobs |
| `sample_skills` | TEXT | - | Sample Skills |
| `cluster_confidence` | REAL | - | Cluster Confidence |
| `silhouette_score` | REAL | - | Silhouette Score |
| `intra_cluster_similarity` | REAL | - | Intra Cluster Similarity |
| `inter_cluster_distance` | REAL | - | Inter Cluster Distance |
| `clustering_algorithm` | TEXT | - | Clustering Algorithm |
| `algorithm_parameters` | TEXT | - | Algorithm Parameters |
| `analysis_date` | TEXT | - | Analysis Date |
| `created_timestamp` | TEXT | - | Created Timestamp |

#### Foreign Key Relationships

- `job_profile_id` references `core_job_architecture.JobProfileID`

#### Sample Data

```json
{
  "job_profile_id": "R0001.5",
  "job_profile": "Payment Systems Analyst - 5",
  "job_function": "Data & Analytics",
  "job_sub_function": "Data Governance",
  "job_category": "Support",
  "management_level": "Group 2",
  "cluster_id": 0,
  "cluster_name": "Operations & Processing - Group 2 Cluster",
  "cluster_description": "Diverse cluster of 644 roles spanning 22 job functions with shared competencies",
  "cluster_rationale": "Clustered based on cross-functional skill similarities despite different job functions",
  "cluster_size": 644,
  "sample_jobs": "Payment Systems Analyst - 5; Settlement Officer - 6; Sales Manager - II",
  "sample_skills": "Skills analysis pending",
  "cluster_confidence": 0.261,
  "silhouette_score": 0.21711856343968797,
  "intra_cluster_similarity": 0.0,
  "inter_cluster_distance": 0.0,
  "clustering_algorithm": "DBSCAN",
  "algorithm_parameters": "eps=0.7300000000000001, min_samples=2",
  "analysis_date": "2025-08-10",
  "created_timestamp": "2025-08-10T19:19:10.813348"
}
```

*(5 sample records available)*

---

### analytics_job_family_characteristics

**Records**: 20

#### Schema

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `cluster_id` | INTEGER | PK, FK | Cluster Id |
| `family_name` | TEXT | - | Family Name |
| `family_description` | TEXT | - | Family Description |
| `family_rationale` | TEXT | - | Family Rationale |
| `cluster_size` | INTEGER | - | Cluster Size |
| `sample_jobs` | TEXT | - | Sample Jobs |
| `sample_skills` | TEXT | - | Sample Skills |
| `core_job_functions` | TEXT | - | Core Job Functions |
| `secondary_job_functions` | TEXT | - | Secondary Job Functions |
| `dominant_function` | TEXT | - | Dominant Function |
| `function_purity` | REAL | - | Function Purity |
| `management_level_pattern` | TEXT | - | Management Level Pattern |
| `specialization_depth` | TEXT | - | Specialization Depth |
| `average_skills_per_job` | REAL | - | Average Skills Per Job |
| `silhouette_score` | REAL | - | Silhouette Score |
| `intra_family_similarity` | REAL | - | Intra Family Similarity |
| `inter_family_separation` | REAL | - | Inter Family Separation |
| `business_value_score` | REAL | - | Business Value Score |
| `career_pathway_potential` | TEXT | - | Career Pathway Potential |
| `skill_transferability` | REAL | - | Skill Transferability |
| `market_demand_level` | TEXT | - | Market Demand Level |
| `typical_career_stage` | TEXT | - | Typical Career Stage |
| `promotion_frequency` | TEXT | - | Promotion Frequency |
| `lateral_movement_potential` | TEXT | - | Lateral Movement Potential |
| `clustering_algorithm` | TEXT | - | Clustering Algorithm |
| `algorithm_parameters` | TEXT | - | Algorithm Parameters |
| `quality_validation_date` | TEXT | - | Quality Validation Date |
| `business_review_date` | TEXT | - | Business Review Date |
| `created_timestamp` | TEXT | - | Created Timestamp |

#### Foreign Key Relationships

- `cluster_id` references `analytics_job_families.cluster_id`

#### Sample Data

```json
{
  "cluster_id": 0,
  "family_name": "Operations & Processing - Group 2 Cluster",
  "family_description": "Diverse cluster of 644 roles spanning 22 job functions with shared competencies",
  "family_rationale": "Clustered based on cross-functional skill similarities despite different job functions",
  "cluster_size": 644,
  "sample_jobs": "Payment Systems Analyst - 5; Settlement Officer - 6; Sales Manager - II",
  "sample_skills": "Skills analysis pending",
  "core_job_functions": "{'Operations & Processing': 71, 'Finance & Treasury': 49, 'Risk Management': 47}",
  "secondary_job_functions": "{'Strategy & Planning': 7, 'Business Development': 7}",
  "dominant_function": "Operations & Processing",
  "function_purity": 0.11,
  "management_level_pattern": "{'Group 2': 156, 'Group 3': 128, 'Group 4': 119, 'Group 1': 105, 'Group 5': 66, 'Group 6': 39, 'Grou...",
  "specialization_depth": "broad",
  "average_skills_per_job": 0.0,
  "silhouette_score": 0.21711856343968797,
  "intra_family_similarity": 0.0,
  "inter_family_separation": 0.0,
  "business_value_score": 0.8,
  "career_pathway_potential": "medium",
  "skill_transferability": 0.7,
  "market_demand_level": "medium",
  "typical_career_stage": "mid",
  "promotion_frequency": "medium",
  "lateral_movement_potential": "high",
  "clustering_algorithm": "DBSCAN",
  "algorithm_parameters": "eps=0.7300000000000001, min_samples=2",
  "quality_validation_date": "2025-08-10T19:19:10.829128",
  "business_review_date": "2025-08-10T19:19:10.829128",
  "created_timestamp": "2025-08-10T19:19:10.829128"
}
```

*(5 sample records available)*

---

### analytics_job_similarities

**Records**: 510,510

#### Schema

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `similarity_id` | TEXT | PK | Similarity Id |
| `job_from` | TEXT | FK | Job From |
| `job_to` | TEXT | FK | Job To |
| `similarity_score` | REAL | - | Similarity Score |
| `enhanced_similarity_score` | REAL | - | Enhanced Similarity Score |
| `rarity_weighted_score` | REAL | - | Rarity Weighted Score |
| `shared_defining_skills_count` | INTEGER | - | Shared Defining Skills Count |
| `defining_skill_boost` | REAL | - | Defining Skill Boost |
| `shared_skills_count` | INTEGER | - | Shared Skills Count |
| `total_skills_from` | INTEGER | - | Total Skills From |
| `total_skills_to` | INTEGER | - | Total Skills To |
| `skill_overlap_percentage` | REAL | - | Skill Overlap Percentage |
| `shared_skills` | TEXT | - | Shared Skills |
| `shared_defining_skills` | TEXT | - | Shared Defining Skills |
| `skill_gap_analysis` | TEXT | - | Skill Gap Analysis |
| `calculation_algorithm` | TEXT | - | Calculation Algorithm |
| `created_timestamp` | TEXT | - | Created Timestamp |

#### Foreign Key Relationships

- `job_to` references `core_job_architecture.JobProfileID`
- `job_from` references `core_job_architecture.JobProfileID`

#### Sample Data

```json
{
  "similarity_id": "R0001.5_R0001.6",
  "job_from": "R0001.5",
  "job_to": "R0001.6",
  "similarity_score": 0.08161369828627027,
  "enhanced_similarity_score": 367.39099999999996,
  "rarity_weighted_score": 367.39099999999996,
  "shared_defining_skills_count": 33,
  "defining_skill_boost": 366.3914,
  "shared_skills_count": 68,
  "total_skills_from": 68,
  "total_skills_to": 68,
  "skill_overlap_percentage": 100.0,
  "shared_skills": "Business Partnering, Microsoft Exchange Server API, Contract Negotiation, Change Management Planning...",
  "shared_defining_skills": "Contract Negotiation, Change Management Planning, Predictive Analytics, Business Administration, Man...",
  "skill_gap_analysis": "Skills needed: 0, Defining gaps: 0",
  "calculation_algorithm": "rarity_weighted_v1.0",
  "created_timestamp": "2025-08-10 09:14:50"
}
```

*(5 sample records available)*

---

### analytics_movement_patterns

**Records**: 21,307

#### Schema

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `movement_pattern_id` | TEXT | PK | Movement Pattern Id |
| `movement_month` | TEXT | - | Movement Month |
| `from_position` | TEXT | - | From Position |
| `to_position` | TEXT | - | To Position |
| `from_job_profile_id` | TEXT | FK | From Job Profile Id |
| `to_job_profile_id` | TEXT | FK | To Job Profile Id |
| `movement_count` | INTEGER | - | Movement Count |
| `unique_employees` | INTEGER | - | Unique Employees |
| `avg_days_between` | REAL | - | Avg Days Between |
| `pct_total_movements` | REAL | - | Pct Total Movements |
| `movement_type` | TEXT | - | Movement Type |
| `skill_similarity_score` | REAL | - | Skill Similarity Score |
| `difficulty_score` | REAL | - | Difficulty Score |
| `success_rate` | REAL | - | Success Rate |
| `created_timestamp` | TEXT | - | Created Timestamp |

#### Foreign Key Relationships

- `to_job_profile_id` references `core_job_architecture.JobProfileID`
- `from_job_profile_id` references `core_job_architecture.JobProfileID`

#### Sample Data

```json
{
  "movement_pattern_id": "pattern_000938",
  "movement_month": "2021-07",
  "from_position": "50002954",
  "to_position": "50002822",
  "from_job_profile_id": "R0264.6",
  "to_job_profile_id": "R0238.0",
  "movement_count": 3,
  "unique_employees": 1,
  "avg_days_between": 0.0,
  "pct_total_movements": 0.31,
  "movement_type": "lateral",
  "skill_similarity_score": null,
  "difficulty_score": null,
  "success_rate": null,
  "created_timestamp": "2025-08-10T19:15:20.891404"
}
```

*(5 sample records available)*

---

### analytics_pathway_predictions

**Records**: 0

#### Schema

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `prediction_id` | TEXT | PK | Prediction Id |
| `from_job_profile_id` | TEXT | FK | From Job Profile Id |
| `to_job_profile_id` | TEXT | FK | To Job Profile Id |
| `ml_predicted_movements` | REAL | - | Ml Predicted Movements |
| `pathway_volume_percentile` | REAL | - | Pathway Volume Percentile |
| `pathway_volume_category` | TEXT | - | Pathway Volume Category |
| `prediction_interval_lower_80pct` | REAL | - | Prediction Interval Lower 80Pct |
| `prediction_interval_upper_80pct` | REAL | - | Prediction Interval Upper 80Pct |
| `prediction_interval_width_80pct` | REAL | - | Prediction Interval Width 80Pct |
| `model_agreement_fraction` | TEXT | - | Model Agreement Fraction |
| `models_agreeing_count` | INTEGER | - | Models Agreeing Count |
| `agreement_rate_decimal` | REAL | - | Agreement Rate Decimal |
| `prediction_random_forest` | REAL | - | Prediction Random Forest |
| `prediction_xgboost` | REAL | - | Prediction Xgboost |
| `prediction_gradient_boosting` | REAL | - | Prediction Gradient Boosting |
| `historical_sample_size` | INTEGER | - | Historical Sample Size |
| `ensemble_standard_deviation` | REAL | - | Ensemble Standard Deviation |
| `prediction_coefficient_of_variation_percent` | REAL | - | Prediction Coefficient Of Variation Percent |
| `from_job_profile_name` | TEXT | - | From Job Profile Name |
| `to_job_profile_name` | TEXT | - | To Job Profile Name |
| `training_algorithm` | TEXT | - | Training Algorithm |
| `training_timestamp` | TEXT | - | Training Timestamp |
| `created_timestamp` | TEXT | - | Created Timestamp |

#### Foreign Key Relationships

- `to_job_profile_id` references `core_job_architecture.JobProfileID`
- `from_job_profile_id` references `core_job_architecture.JobProfileID`
---

### analytics_skill_bundles

**Records**: 2,057

#### Schema

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `skill_id` | TEXT | PK, FK | Skill Id |
| `skill_name` | TEXT | - | Skill Name |
| `category` | TEXT | - | Category |
| `subcategory` | TEXT | - | Subcategory |
| `skill_type` | TEXT | - | Skill Type |
| `total_occurrences` | INTEGER | - | Total Occurrences |
| `jobs_count` | INTEGER | - | Jobs Count |
| `prevalence_percent` | REAL | - | Prevalence Percent |
| `cluster_id` | INTEGER | PK | Cluster Id |
| `bundle_name` | TEXT | - | Bundle Name |
| `bundle_description` | TEXT | - | Bundle Description |
| `bundle_rationale` | TEXT | - | Bundle Rationale |
| `bundle_size` | INTEGER | - | Bundle Size |
| `is_specialized` | BOOLEAN | - | Is Specialized |
| `sample_skills` | TEXT | - | Sample Skills |
| `sample_job_functions` | TEXT | - | Sample Job Functions |
| `bundle_confidence` | REAL | - | Bundle Confidence |
| `silhouette_score` | REAL | - | Silhouette Score |
| `intra_bundle_similarity` | REAL | - | Intra Bundle Similarity |
| `inter_bundle_distance` | REAL | - | Inter Bundle Distance |
| `clustering_algorithm` | TEXT | - | Clustering Algorithm |
| `similarity_method` | TEXT | - | Similarity Method |
| `algorithm_parameters` | TEXT | - | Algorithm Parameters |
| `analysis_date` | TEXT | - | Analysis Date |
| `created_timestamp` | TEXT | - | Created Timestamp |

#### Foreign Key Relationships

- `skill_id` references `core_skills_taxonomy.Skill_ID`

#### Sample Data

```json
{
  "skill_id": "ES439D5D4E1DA572EFB8",
  "skill_name": "Customer Centricity",
  "category": "Analysis",
  "subcategory": "Business Intelligence",
  "skill_type": "Specialized Skill",
  "total_occurrences": 666,
  "jobs_count": 666,
  "prevalence_percent": 93.15,
  "cluster_id": 0,
  "bundle_name": "Analysis Skills Bundle (91 skills)",
  "bundle_description": "Collection of Analysis skills with 3.1% average prevalence",
  "bundle_rationale": "Grouped by Analysis category similarity",
  "bundle_size": 91,
  "is_specialized": 0,
  "sample_skills": "Customer Centricity; Data Analysis; Data Literacy",
  "sample_job_functions": "Analysis pending",
  "bundle_confidence": null,
  "silhouette_score": null,
  "intra_bundle_similarity": null,
  "inter_bundle_distance": null,
  "clustering_algorithm": null,
  "similarity_method": null,
  "algorithm_parameters": null,
  "analysis_date": null,
  "created_timestamp": "2025-08-10T19:19:10.988391"
}
```

*(5 sample records available)*

---

### analytics_skill_demand_trends

**Records**: 0

#### Schema

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `skill_id` | TEXT | PK, FK | Skill Id |
| `skill_name` | TEXT | - | Skill Name |
| `category` | TEXT | - | Category |
| `skill_type` | TEXT | - | Skill Type |
| `jobs_requiring_skill` | INTEGER | - | Jobs Requiring Skill |
| `total_skill_instances` | INTEGER | - | Total Skill Instances |
| `current_prevalence_percent` | REAL | - | Current Prevalence Percent |
| `short_term_cagr` | REAL | - | Short Term Cagr |
| `medium_term_cagr` | REAL | - | Medium Term Cagr |
| `long_term_cagr` | REAL | - | Long Term Cagr |
| `velocity_category` | TEXT | - | Velocity Category |
| `trend_direction` | TEXT | - | Trend Direction |
| `trend_strength` | TEXT | - | Trend Strength |
| `trend_confidence` | REAL | - | Trend Confidence |
| `total_movements` | INTEGER | - | Total Movements |
| `total_recency_weighted_movements` | REAL | - | Total Recency Weighted Movements |
| `recency_weighted_growth_pct` | REAL | - | Recency Weighted Growth Pct |
| `projected_demand_1yr` | REAL | - | Projected Demand 1Yr |
| `projected_demand_2yr` | REAL | - | Projected Demand 2Yr |
| `projected_demand_3yr` | REAL | - | Projected Demand 3Yr |
| `analysis_windows` | TEXT | - | Analysis Windows |
| `velocity_thresholds` | TEXT | - | Velocity Thresholds |
| `data_quality_score` | REAL | - | Data Quality Score |
| `analysis_date` | TEXT | - | Analysis Date |
| `created_timestamp` | TEXT | - | Created Timestamp |

#### Foreign Key Relationships

- `skill_id` references `core_skills_taxonomy.Skill_ID`
---

### analytics_skill_rarity

**Records**: 2,059

#### Schema

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `skill_id` | TEXT | PK, FK | Skill Id |
| `skill_name` | TEXT | - | Skill Name |
| `category` | TEXT | - | Category |
| `subcategory` | TEXT | - | Subcategory |
| `skill_type` | TEXT | - | Skill Type |
| `total_profiles_with_skill` | INTEGER | - | Total Profiles With Skill |
| `total_jobs` | INTEGER | - | Total Jobs |
| `prevalence_percentage` | REAL | - | Prevalence Percentage |
| `rarity_category` | TEXT | - | Rarity Category |
| `rarity_score` | REAL | - | Rarity Score |
| `is_defining_skill` | BOOLEAN | - | Is Defining Skill |
| `defining_for_jobs_count` | INTEGER | - | Defining For Jobs Count |
| `defining_for_jobs` | TEXT | - | Defining For Jobs |
| `analysis_date` | TEXT | - | Analysis Date |
| `algorithm_version` | TEXT | - | Algorithm Version |
| `created_timestamp` | TEXT | - | Created Timestamp |

#### Foreign Key Relationships

- `skill_id` references `core_skills_taxonomy.Skill_ID`

#### Sample Data

```json
{
  "skill_id": "BGS11665AC6BD06C5EBD",
  "skill_name": "Payroll Reporting",
  "category": "Human Resources",
  "subcategory": "Payroll",
  "skill_type": "Specialized Skill",
  "total_profiles_with_skill": 1,
  "total_jobs": 715,
  "prevalence_percentage": 0.14,
  "rarity_category": "Rare",
  "rarity_score": 99.86,
  "is_defining_skill": 1,
  "defining_for_jobs_count": 0,
  "defining_for_jobs": "",
  "analysis_date": "2025-08-10",
  "algorithm_version": "rarity_analyzer_v1.0",
  "created_timestamp": "2025-08-10 09:15:08"
}
```

*(5 sample records available)*

---

### analytics_specialized_skills

**Records**: 0

#### Schema

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `skill_id` | TEXT | PK, FK | Skill Id |
| `skill_name` | TEXT | - | Skill Name |
| `category` | TEXT | - | Category |
| `subcategory` | TEXT | - | Subcategory |
| `skill_type` | TEXT | - | Skill Type |
| `jobs_count` | INTEGER | - | Jobs Count |
| `prevalence_percent` | REAL | - | Prevalence Percent |
| `specialization_score` | REAL | - | Specialization Score |
| `rarity_rank` | INTEGER | - | Rarity Rank |
| `specialization_reason` | TEXT | - | Specialization Reason |
| `specialization_category` | TEXT | - | Specialization Category |
| `market_context` | TEXT | - | Market Context |
| `strategic_importance` | TEXT | - | Strategic Importance |
| `skill_lifecycle_stage` | TEXT | - | Skill Lifecycle Stage |
| `investment_recommendation` | TEXT | - | Investment Recommendation |
| `related_skills` | TEXT | - | Related Skills |
| `typical_job_functions` | TEXT | - | Typical Job Functions |
| `training_availability` | TEXT | - | Training Availability |
| `external_market_demand` | TEXT | - | External Market Demand |
| `analysis_methodology` | TEXT | - | Analysis Methodology |
| `confidence_level` | TEXT | - | Confidence Level |
| `last_review_date` | TEXT | - | Last Review Date |
| `next_review_date` | TEXT | - | Next Review Date |
| `created_timestamp` | TEXT | - | Created Timestamp |

#### Foreign Key Relationships

- `skill_id` references `core_skills_taxonomy.Skill_ID`
---

## core Tables

### core_job_architecture

**Records**: 715

#### Schema

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `JobProfileID` | TEXT | PK | Jobprofileid |
| `JobProfile` | TEXT | - | Jobprofile |
| `JobFunction` | TEXT | - | Jobfunction |
| `JobCategory` | TEXT | - | Jobcategory |
| `ManagementLevel` | TEXT | - | Managementlevel |
| `JobID` | TEXT | - | Jobid |
| `Job` | TEXT | - | Job |
| `ProfileTitleSuffix` | TEXT | - | Profiletitlesuffix |
| `JobSubFunctionID` | TEXT | - | Jobsubfunctionid |
| `JobSubFunction` | TEXT | - | Jobsubfunction |
| `JobFunctionID` | TEXT | - | Jobfunctionid |
| `JobCategoryID` | TEXT | - | Jobcategoryid |
| `Customer_Facing` | TEXT | - | Customer Facing |
| `is_Banker` | TEXT | - | Is Banker |
| `Executive_Leadership_Group` | TEXT | - | Executive Leadership Group |
| `Accountability_Scope` | TEXT | - | Accountability Scope |
| `created_timestamp` | TEXT | - | Created Timestamp |
| `updated_timestamp` | TEXT | - | Updated Timestamp |

#### Sample Data

```json
{
  "JobProfileID": "R0001.5",
  "JobProfile": "Payment Systems Analyst - 5",
  "JobFunction": "Data & Analytics",
  "JobCategory": "Support",
  "ManagementLevel": "Group 2",
  "JobID": "R0001",
  "Job": "Payment Systems Analyst",
  "ProfileTitleSuffix": "Senior Manager",
  "JobSubFunctionID": "JF0655",
  "JobSubFunction": "Data Governance",
  "JobFunctionID": "JF016",
  "JobCategoryID": "JC2",
  "Customer_Facing": "Customer Facing",
  "is_Banker": "Non-Banker",
  "Executive_Leadership_Group": "",
  "Accountability_Scope": "",
  "created_timestamp": "2025-08-10 09:00:42",
  "updated_timestamp": "2025-08-10 09:00:42"
}
```

*(5 sample records available)*

---

### core_job_skill_requirements

**Records**: 40,170

#### Schema

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `JobProfileID` | TEXT | PK, FK | Jobprofileid |
| `Skill_ID` | TEXT | PK, FK | Skill Id |
| `created_timestamp` | TEXT | - | Created Timestamp |

#### Foreign Key Relationships

- `Skill_ID` references `core_skills_taxonomy.Skill_ID`
- `JobProfileID` references `core_job_architecture.JobProfileID`

#### Sample Data

```json
{
  "JobProfileID": "R0001.5",
  "Skill_ID": "BGSD16A8EEF4F5775E15",
  "created_timestamp": "2025-08-10 09:00:43"
}
```

*(5 sample records available)*

---

### core_skills_taxonomy

**Records**: 38,525

#### Schema

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `Skill_ID` | TEXT | PK | Skill Id |
| `Skill_Name` | TEXT | - | Skill Name |
| `Category` | TEXT | - | Category |
| `Subcategory` | TEXT | - | Subcategory |
| `SkillType` | TEXT | - | Skilltype |
| `category_id` | REAL | - | Category Id |
| `description` | TEXT | - | Description |
| `descriptionSource` | TEXT | - | Descriptionsource |
| `infoUrl` | TEXT | - | Infourl |
| `isLanguage` | BOOLEAN | - | Islanguage |
| `isSoftware` | BOOLEAN | - | Issoftware |
| `source_version` | REAL | - | Source Version |
| `subcategory_id` | REAL | - | Subcategory Id |
| `tag_wikipediaExtract` | TEXT | - | Tag Wikipediaextract |
| `tag_wikipediaUrl` | TEXT | - | Tag Wikipediaurl |
| `tags` | TEXT | - | Tags |
| `type` | TEXT | - | Type |
| `type_id` | TEXT | - | Type Id |
| `created_timestamp` | TEXT | - | Created Timestamp |
| `updated_timestamp` | TEXT | - | Updated Timestamp |

#### Sample Data

```json
{
  "Skill_ID": "BGS1024316C916ACCFA3",
  "Skill_Name": "DX Spectrum",
  "Category": "Information Technology",
  "Subcategory": "Enterprise Information Management",
  "SkillType": "Specialized Skill",
  "category_id": 17.0,
  "description": "",
  "descriptionSource": "",
  "infoUrl": "https://lightcast.io/open-skills/skills/BGS1024316C916ACCFA3",
  "isLanguage": 0,
  "isSoftware": 1,
  "source_version": 8.5,
  "subcategory_id": 411.0,
  "tag_wikipediaExtract": "",
  "tag_wikipediaUrl": "",
  "tags": "[]",
  "type": "{"id": "ST1", "name": "Specialized Skill"}",
  "type_id": "ST1",
  "created_timestamp": "2025-08-10 09:00:42",
  "updated_timestamp": "2025-08-10 09:00:42"
}
```

*(5 sample records available)*

---

### core_workforce_current

**Records**: 35,000

#### Schema

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `employee_number` | TEXT | PK | Employee Number |
| `position_number` | TEXT | - | Position Number |
| `position_name` | TEXT | - | Position Name |
| `JobProfileID` | TEXT | FK | Jobprofileid |
| `Employee_Group` | TEXT | - | Employee Group |
| `Employee_Subgroup` | TEXT | - | Employee Subgroup |
| `Salary_Group` | TEXT | - | Salary Group |
| `Location` | TEXT | - | Location |
| `Rg` | TEXT | - | Rg |
| `Cty` | TEXT | - | Cty |
| `ORG_UNIT_NAME_1` | TEXT | - | Org Unit Name 1 |
| `ORG_UNIT_NAME_2` | TEXT | - | Org Unit Name 2 |
| `ORG_UNIT_NAME_3` | TEXT | - | Org Unit Name 3 |
| `ORG_UNIT_NAME_4` | TEXT | - | Org Unit Name 4 |
| `ORG_UNIT_NAME_5` | TEXT | - | Org Unit Name 5 |
| `ORG_UNIT_NAME_6` | TEXT | - | Org Unit Name 6 |
| `ORG_UNIT_NAME_7` | TEXT | - | Org Unit Name 7 |
| `ORG_UNIT_NAME_8` | TEXT | - | Org Unit Name 8 |
| `ORG_UNIT_NAME_9` | TEXT | - | Org Unit Name 9 |
| `ORG_UNIT_NAME_10` | TEXT | - | Org Unit Name 10 |
| `created_timestamp` | TEXT | - | Created Timestamp |

#### Foreign Key Relationships

- `JobProfileID` references `core_job_architecture.JobProfileID`

#### Sample Data

```json
{
  "employee_number": "100000",
  "position_number": "50003311",
  "position_name": "Investment Principal Specialist",
  "JobProfileID": "R0242.3",
  "Employee_Group": "Fixed Term",
  "Employee_Subgroup": "Full Time",
  "Salary_Group": "Group 7",
  "Location": "Brisbane City",
  "Rg": "QLD",
  "Cty": "AU",
  "ORG_UNIT_NAME_1": "National Australia Bank Limited",
  "ORG_UNIT_NAME_2": "Corporate & Institutional Banking",
  "ORG_UNIT_NAME_3": "Technology",
  "ORG_UNIT_NAME_4": "Business Banking Operations",
  "ORG_UNIT_NAME_5": "Team 15",
  "ORG_UNIT_NAME_6": "Squad H",
  "ORG_UNIT_NAME_7": "Pod 15",
  "ORG_UNIT_NAME_8": "Unit 038",
  "ORG_UNIT_NAME_9": "Cell 11",
  "ORG_UNIT_NAME_10": "Node 024",
  "created_timestamp": "2025-08-10 09:00:44"
}
```

*(5 sample records available)*

---

## system Tables

### sys_schema_metadata

**Records**: 25

#### Schema

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `metadata_key` | TEXT | PK | Metadata Key |
| `metadata_value` | TEXT | - | Metadata Value |
| `metadata_category` | TEXT | - | Metadata Category |
| `description` | TEXT | - | Description |
| `created_timestamp` | TEXT | - | Created Timestamp |
| `updated_timestamp` | TEXT | - | Updated Timestamp |

#### Sample Data

```json
{
  "metadata_key": "schema_version",
  "metadata_value": "2.0",
  "metadata_category": "schema",
  "description": "Enhanced database schema version",
  "created_timestamp": "2025-08-10 09:00:42",
  "updated_timestamp": "2025-08-10 09:00:42"
}
```

*(5 sample records available)*

---
