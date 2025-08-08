# SQLite Schema Design for NAB Skill Similarity Engine
## Workforce Intelligence Database

**Generated**: 2025-08-08 15:23:21
**Database File**: `C:\Users\kipjo\OneDrive\Documents\GitHub\skill-similarity-engine\models\2025-Q3\business_context.sqlite`
**Database Size**: 1750.55 MB
**SQLite Version**: 3.45.3
**Page Size**: 4096 bytes
**Total Pages**: 448,141
**Foreign Keys**: Disabled
**Last Modified**: 2025-08-08T13:51:05.840376

---

## Overview

This document provides comprehensive schema documentation for the NAB Skill Similarity Engine SQLite database.
The database integrates job architecture, skill taxonomies, workforce context, movement analysis, and pre-computed similarities
to support career pathway analysis, workforce planning, and strategic workforce intelligence.

## Quick Reference for LLMs

**Core Tables for Query Development:**

- **`analytics_job_similarities`** (510,510 records) - job_from, job_to, similarity_score
- **`analytics_movement_patterns`** (25,608 records) - movement_pattern, movement_count, month, avg_days_in_position
- **`core_colleague_positions_history`** (899,675 records) - Employee Number, Position Number, Week Ending, PosIDLookupKey
- **`core_job_architecture`** (715 records) - JobProfileID, JobProfile, JobFamily, JobFamilyGroup
- **`core_job_skill_requirements`** (40,170 records) - JobProfileID, Skill_ID, Skill_Weight
- **`core_skills_taxonomy`** (38,525 records) - Skill_ID, Skill_Name, Category, SkillType
- **`core_workforce_current`** (35,000 records) - JobProfileID, Division, Business_Unit, Location, Team

**Key Relationships:**
- `jobs.JobProfileID` â†’ `career_pathways.source_job_id/target_job_id`
- `jobs.JobProfileID` â†’ `job_similarities.job_from/job_to`
- `jobs.JobProfileID` â†’ `positions.JobProfileID`
- `jobs.JobProfileID` â†’ `job_skills.JobProfileID`
- `skills.Skill_ID` â†’ `job_skills.Skill_ID`

**Critical for D3 Tree Queries:**
- Use `career_pathways` table for pre-computed relationships (fast!)
- `similarity_rank` 1-12 gives top pathways per job
- `career_move_type`: 'lateral', 'progression', 'cross_family'
- Handle quoted column names: `"Position Number"`, `"Business_Unit"`

---

## Database Statistics

- **Total Tables**: 17
- **Total Records**: 2,054,511
- **Total Indexes**: 55
- **Database Size**: 1750.55 MB

### Key Business Metrics


## Relationship Analysis

### Foreign Key Relationships (17)

- `analytics_job_defining_skills.skill_id` → `core_skills_taxonomy.Skill_ID`
- `analytics_job_defining_skills.job_profile_id` → `core_job_architecture.JobProfileID`
- `analytics_job_families.job_profile_id` → `core_job_architecture.JobProfileID`
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
- `core_position_timeline.JobProfileID` → `core_job_architecture.JobProfileID`
- `core_workforce_current.JobProfileID` → `core_job_architecture.JobProfileID`

### Referential Integrity Check

- ✅ **analytics_job_defining_skills.skill_id**: No orphaned records
- ✅ **analytics_job_defining_skills.job_profile_id**: No orphaned records
- ✅ **analytics_job_families.job_profile_id**: No orphaned records
- ✅ **analytics_job_similarities.job_to**: No orphaned records
- ✅ **analytics_job_similarities.job_from**: No orphaned records
- ✅ **analytics_movement_patterns.to_job_profile_id**: No orphaned records
- ✅ **analytics_movement_patterns.from_job_profile_id**: No orphaned records
- ✅ **analytics_pathway_predictions.to_job_profile_id**: No orphaned records
- ✅ **analytics_pathway_predictions.from_job_profile_id**: No orphaned records
- ✅ **analytics_skill_bundles.skill_id**: No orphaned records
- ✅ **analytics_skill_demand_trends.skill_id**: No orphaned records
- ✅ **analytics_skill_rarity.skill_id**: No orphaned records
- ✅ **analytics_specialized_skills.skill_id**: No orphaned records
- ⚠️ **core_job_skill_requirements.Skill_ID**: 125 orphaned records
- ✅ **core_job_skill_requirements.JobProfileID**: No orphaned records
- ✅ **core_position_timeline.JobProfileID**: No orphaned records
- ✅ **core_workforce_current.JobProfileID**: No orphaned records

## Performance Analysis

### Table Size Categories

**Small Tables:**
- analytics_bundle_characteristics: 27 rows
- analytics_job_families: 715 rows
- analytics_pathway_predictions: 0 rows
- analytics_skill_demand_trends: 0 rows
- analytics_specialized_skills: 0 rows
- core_job_architecture: 715 rows
- sys_schema_metadata: 22 rows

**Medium Tables:**
- analytics_job_defining_skills: 19,460 rows
- analytics_movement_patterns: 25,608 rows
- analytics_skill_bundles: 2,057 rows
- analytics_skill_rarity: 2,059 rows
- core_job_skill_requirements: 40,170 rows
- core_skills_taxonomy: 38,525 rows
- core_workforce_current: 35,000 rows

**Large Tables:**
- analytics_job_similarities: 510,510 rows
- core_colleague_positions_history: 899,675 rows
- core_position_timeline: 479,968 rows

### Query Optimization Recommendations

- **foreign_key_indexing**: Foreign key column 'skill_id' not indexed
  - Recommendation: CREATE INDEX idx_analytics_skill_bundles_skill_id ON analytics_skill_bundles(skill_id)
- **foreign_key_indexing**: Foreign key column 'skill_id' not indexed
  - Recommendation: CREATE INDEX idx_analytics_skill_rarity_skill_id ON analytics_skill_rarity(skill_id)

## Entity Relationship Diagram

```mermaid
erDiagram
    ANALYTICS_BUNDLE_CHARACTERISTICS {
        integer cluster_id PK
        text bundle_name
        text bundle_description
        text bundle_rationale
        integer bundle_size
        text sample_skills
        text sample_job_functions
        text core_skills
        text peripheral_skills
        text dominant_category
        real category_purity
        text application_level
        text specialization_area
        real average_jobs_per_skill
        real taxonomy_alignment_score
        real silhouette_score
        real intra_bundle_cohesion
        real inter_bundle_separation
        real business_value_score
        text training_feasibility
        real skill_complementarity
        text market_demand_level
        text common_job_families
        text typical_career_stage
        text skill_acquisition_difficulty
        text clustering_algorithm
        text algorithm_parameters
        text quality_validation_date
        text business_review_date
        text created_timestamp
    }

    ANALYTICS_JOB_DEFINING_SKILLS {
        text job_profile_id PK FK
        text skill_id PK FK
        text skill_name
        text job_profile
        text category
        text subcategory
        text skill_type
        real prevalence_percentage
        integer total_profiles_with_skill
        text rarity_category
        integer defining_skill_rank
        real defining_skill_score
        text analysis_date
        real percentile_threshold
        text created_timestamp
    }

    ANALYTICS_JOB_FAMILIES {
        text job_profile_id PK FK
        text job_profile
        text job_function
        text job_sub_function
        text job_category
        text management_level
        integer cluster_id PK
        text cluster_name
        text cluster_description
        text cluster_rationale
        integer cluster_size
        text sample_jobs
        text sample_skills
        real cluster_confidence
        real silhouette_score
        real intra_cluster_similarity
        real inter_cluster_distance
        text clustering_algorithm
        text algorithm_parameters
        text analysis_date
        text created_timestamp
    }

    ANALYTICS_JOB_SIMILARITIES {
        text similarity_id PK
        text job_from FK
        text job_to FK
        real similarity_score
        real enhanced_similarity_score
        real rarity_weighted_score
        integer shared_defining_skills_count
        real defining_skill_boost
        integer shared_skills_count
        integer total_skills_from
        integer total_skills_to
        real skill_overlap_percentage
        text shared_skills
        text shared_defining_skills
        text skill_gap_analysis
        text calculation_algorithm
        text created_timestamp
    }

    ANALYTICS_MOVEMENT_PATTERNS {
        text movement_pattern_id PK
        text movement_month
        text from_position
        text to_position
        text from_job_profile_id FK
        text to_job_profile_id FK
        integer movement_count
        integer unique_employees
        real avg_days_between
        real pct_total_movements
        text movement_type
        real skill_similarity_score
        real difficulty_score
        real success_rate
        text created_timestamp
    }

    ANALYTICS_PATHWAY_PREDICTIONS {
        text prediction_id PK
        text from_job_profile_id FK
        text to_job_profile_id FK
        real ml_predicted_movements
        real pathway_volume_percentile
        text pathway_volume_category
        real prediction_interval_lower_80pct
        real prediction_interval_upper_80pct
        real prediction_interval_width_80pct
        text model_agreement_fraction
        integer models_agreeing_count
        real agreement_rate_decimal
        real prediction_random_forest
        real prediction_xgboost
        real prediction_gradient_boosting
        integer historical_sample_size
        real ensemble_standard_deviation
        real prediction_coefficient_of_variation_percent
        text from_job_profile_name
        text to_job_profile_name
        text training_algorithm
        text training_timestamp
        text created_timestamp
    }

    ANALYTICS_SKILL_BUNDLES {
        text skill_id PK FK
        text skill_name
        text category
        text subcategory
        text skill_type
        integer total_occurrences
        integer jobs_count
        real prevalence_percent
        integer cluster_id PK
        text bundle_name
        text bundle_description
        text bundle_rationale
        integer bundle_size
        boolean is_specialized
        text sample_skills
        text sample_job_functions
        real bundle_confidence
        real silhouette_score
        real intra_bundle_similarity
        real inter_bundle_distance
        text clustering_algorithm
        text similarity_method
        text algorithm_parameters
        text analysis_date
        text created_timestamp
    }

    ANALYTICS_SKILL_DEMAND_TRENDS {
        text skill_id PK FK
        text skill_name
        text category
        text skill_type
        integer jobs_requiring_skill
        integer total_skill_instances
        real current_prevalence_percent
        real short_term_cagr
        real medium_term_cagr
        real long_term_cagr
        text velocity_category
        text trend_direction
        text trend_strength
        real trend_confidence
        integer total_movements
        real total_recency_weighted_movements
        real recency_weighted_growth_pct
        real projected_demand_1yr
        real projected_demand_2yr
        real projected_demand_3yr
        text analysis_windows
        text velocity_thresholds
        real data_quality_score
        text analysis_date
        text created_timestamp
    }

    ANALYTICS_SKILL_RARITY {
        text skill_id PK FK
        text skill_name
        text category
        text subcategory
        text skill_type
        integer total_profiles_with_skill
        integer total_jobs
        real prevalence_percentage
        text rarity_category
        real rarity_score
        boolean is_defining_skill
        integer defining_for_jobs_count
        text defining_for_jobs
        text analysis_date
        text algorithm_version
        text created_timestamp
    }

    ANALYTICS_SPECIALIZED_SKILLS {
        text skill_id PK FK
        text skill_name
        text category
        text subcategory
        text skill_type
        integer jobs_count
        real prevalence_percent
        real specialization_score
        integer rarity_rank
        text specialization_reason
        text specialization_category
        text market_context
        text strategic_importance
        text skill_lifecycle_stage
        text investment_recommendation
        text related_skills
        text typical_job_functions
        text training_availability
        text external_market_demand
        text analysis_methodology
        text confidence_level
        text last_review_date
        text next_review_date
        text created_timestamp
    }

    CORE_COLLEAGUE_POSITIONS_HISTORY {
        text Week_Ending PK
        integer Employee_Number
        boolean Operational
        text Position_Start_Date
        real PosIDLookupKey PK
        integer Position_Number
        text created_timestamp
    }

    CORE_JOB_ARCHITECTURE {
        text JobProfileID PK
        text JobProfile
        text JobFunction
        text JobCategory
        text ManagementLevel
        text JobID
        text Job
        text ProfileTitleSuffix
        text JobSubFunctionID
        text JobSubFunction
        text JobFunctionID
        text JobCategoryID
        text Customer_Facing
        text is_Banker
        text Executive_Leadership_Group
        text Accountability_Scope
        text created_timestamp
        text updated_timestamp
    }

    CORE_JOB_SKILL_REQUIREMENTS {
        text JobProfileID PK FK
        text Skill_ID PK FK
        text created_timestamp
    }

    CORE_POSITION_TIMELINE {
        text position_timeline_id PK
        text Week_Ending
        integer Position_Number
        text JobProfileID FK
        real PosIDLookupKey
        text Organisational_Unit
        integer Cost_Centre_Number
        text Position_Title
        real People_Leader
        boolean Operational
        integer OrgUnitIDLookupKey
        text created_timestamp
    }

    CORE_SKILLS_TAXONOMY {
        text Skill_ID PK
        text Skill_Name
        text Category
        text Subcategory
        text SkillType
        real category_id
        text description
        text descriptionSource
        text infoUrl
        boolean isLanguage
        boolean isSoftware
        real source_version
        real subcategory_id
        text tag_wikipediaExtract
        text tag_wikipediaUrl
        text tags
        text type
        text type_id
        text created_timestamp
        text updated_timestamp
    }

    CORE_WORKFORCE_CURRENT {
        text employee_number PK
        text position_number
        text position_name
        text JobProfileID FK
        text Employee_Group
        text Employee_Subgroup
        text Salary_Group
        text Location
        text Rg
        text Cty
        text ORG_UNIT_NAME_1
        text ORG_UNIT_NAME_2
        text ORG_UNIT_NAME_3
        text ORG_UNIT_NAME_4
        text ORG_UNIT_NAME_5
        text ORG_UNIT_NAME_6
        text ORG_UNIT_NAME_7
        text ORG_UNIT_NAME_8
        text ORG_UNIT_NAME_9
        text ORG_UNIT_NAME_10
        text created_timestamp
    }

    SYS_SCHEMA_METADATA {
        text metadata_key PK
        text metadata_value
        text metadata_category
        text description
        text created_timestamp
        text updated_timestamp
    }

    CORE_SKILLS_TAXONOMY ||--o{ ANALYTICS_JOB_DEFINING_SKILLS : "skill_id"
    CORE_JOB_ARCHITECTURE ||--o{ ANALYTICS_JOB_DEFINING_SKILLS : "job_profile_id"
    CORE_JOB_ARCHITECTURE ||--o{ ANALYTICS_JOB_FAMILIES : "job_profile_id"
    CORE_JOB_ARCHITECTURE ||--o{ ANALYTICS_JOB_SIMILARITIES : "job_to"
    CORE_JOB_ARCHITECTURE ||--o{ ANALYTICS_JOB_SIMILARITIES : "job_from"
    CORE_JOB_ARCHITECTURE ||--o{ ANALYTICS_MOVEMENT_PATTERNS : "to_job_profile_id"
    CORE_JOB_ARCHITECTURE ||--o{ ANALYTICS_MOVEMENT_PATTERNS : "from_job_profile_id"
    CORE_JOB_ARCHITECTURE ||--o{ ANALYTICS_PATHWAY_PREDICTIONS : "to_job_profile_id"
    CORE_JOB_ARCHITECTURE ||--o{ ANALYTICS_PATHWAY_PREDICTIONS : "from_job_profile_id"
    CORE_SKILLS_TAXONOMY ||--o{ ANALYTICS_SKILL_BUNDLES : "skill_id"
    CORE_SKILLS_TAXONOMY ||--o{ ANALYTICS_SKILL_DEMAND_TRENDS : "skill_id"
    CORE_SKILLS_TAXONOMY ||--o{ ANALYTICS_SKILL_RARITY : "skill_id"
    CORE_SKILLS_TAXONOMY ||--o{ ANALYTICS_SPECIALIZED_SKILLS : "skill_id"
    CORE_SKILLS_TAXONOMY ||--o{ CORE_JOB_SKILL_REQUIREMENTS : "Skill_ID"
    CORE_JOB_ARCHITECTURE ||--o{ CORE_JOB_SKILL_REQUIREMENTS : "JobProfileID"
    CORE_JOB_ARCHITECTURE ||--o{ CORE_POSITION_TIMELINE : "JobProfileID"
    CORE_JOB_ARCHITECTURE ||--o{ CORE_WORKFORCE_CURRENT : "JobProfileID"
```

---

## Table Definitions

### 1. **analytics_bundle_characteristics** - 27 records

```sql
CREATE TABLE analytics_bundle_characteristics (
    cluster_id INTEGER PRIMARY KEY,
    bundle_name TEXT,
    bundle_description TEXT,
    bundle_rationale TEXT,
    bundle_size INTEGER,
    sample_skills TEXT,
    sample_job_functions TEXT,
    core_skills TEXT,
    peripheral_skills TEXT,
    dominant_category TEXT,
    category_purity REAL,
    application_level TEXT,
    specialization_area TEXT,
    average_jobs_per_skill REAL,
    taxonomy_alignment_score REAL,
    silhouette_score REAL,
    intra_bundle_cohesion REAL,
    inter_bundle_separation REAL,
    business_value_score REAL,
    training_feasibility TEXT,
    skill_complementarity REAL,
    market_demand_level TEXT,
    common_job_families TEXT,
    typical_career_stage TEXT,
    skill_acquisition_difficulty TEXT,
    clustering_algorithm TEXT,
    algorithm_parameters TEXT,
    quality_validation_date TEXT,
    business_review_date TEXT,
    created_timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);
```

**Column Statistics:**

- **cluster_id**: 27 unique values (27 non-null), range 0 - 26
- **bundle_name**: 27 unique values (27 non-null), avg length 48.11
- **bundle_description**: 27 unique values (27 non-null), avg length 72.04
- **bundle_rationale**: 27 unique values (27 non-null), avg length 42.04
- **bundle_size**: 24 unique values (27 non-null), range 3 - 456
- **sample_skills**: 27 unique values (27 non-null), avg length 67.44
- **sample_job_functions**: 1 unique values (27 non-null), avg length 16.0
- **core_skills**: 0 unique values (0 non-null), avg length 0
- **peripheral_skills**: 0 unique values (0 non-null), avg length 0
- **dominant_category**: 27 unique values (27 non-null), avg length 22.04
- **category_purity**: 1 unique values (27 non-null), range 1.0000 - 1.0000, avg 1.0000
- **application_level**: 1 unique values (27 non-null), avg length 8.0
- **specialization_area**: 27 unique values (27 non-null), avg length 22.04
- **average_jobs_per_skill**: 26 unique values (27 non-null), range 3.0000 - 47.5938, avg 13.9283
- **taxonomy_alignment_score**: 1 unique values (27 non-null), range 0.8000 - 0.8000, avg 0.8000
- **silhouette_score**: 1 unique values (27 non-null), range 0.0000 - 0.0000, avg 0.0000
- **intra_bundle_cohesion**: 0 unique values (0 non-null), range 0.0000 - 0.0000, avg 0.0000
- **inter_bundle_separation**: 0 unique values (0 non-null), range 0.0000 - 0.0000, avg 0.0000
- **business_value_score**: 0 unique values (0 non-null), range 0.0000 - 0.0000, avg 0.0000
- **training_feasibility**: 0 unique values (0 non-null), avg length 0
- **skill_complementarity**: 0 unique values (0 non-null), range 0.0000 - 0.0000, avg 0.0000
- **market_demand_level**: 0 unique values (0 non-null), avg length 0
- **common_job_families**: 0 unique values (0 non-null), avg length 0
- **typical_career_stage**: 0 unique values (0 non-null), avg length 0
- **skill_acquisition_difficulty**: 0 unique values (0 non-null), avg length 0
- **clustering_algorithm**: 0 unique values (0 non-null), avg length 0
- **algorithm_parameters**: 0 unique values (0 non-null), avg length 0
- **quality_validation_date**: 0 unique values (0 non-null), avg length 0
- **business_review_date**: 0 unique values (0 non-null), avg length 0
- **created_timestamp**: 19 unique values (27 non-null), avg length 26.0

**Data Quality - Completeness:**

- **cluster_id**: 100% complete
- **bundle_name**: 100% complete
- **bundle_description**: 100% complete
- **bundle_rationale**: 100% complete
- **bundle_size**: 100% complete
- **sample_skills**: 100% complete
- **sample_job_functions**: 100% complete
- **core_skills**: 0.0% complete (27 null values)
- **peripheral_skills**: 0.0% complete (27 null values)
- **dominant_category**: 100% complete
- **category_purity**: 100% complete
- **application_level**: 100% complete
- **specialization_area**: 100% complete
- **average_jobs_per_skill**: 100% complete
- **taxonomy_alignment_score**: 100% complete
- **silhouette_score**: 100% complete
- **intra_bundle_cohesion**: 0.0% complete (27 null values)
- **inter_bundle_separation**: 0.0% complete (27 null values)
- **business_value_score**: 0.0% complete (27 null values)
- **training_feasibility**: 0.0% complete (27 null values)
- **skill_complementarity**: 0.0% complete (27 null values)
- **market_demand_level**: 0.0% complete (27 null values)
- **common_job_families**: 0.0% complete (27 null values)
- **typical_career_stage**: 0.0% complete (27 null values)
- **skill_acquisition_difficulty**: 0.0% complete (27 null values)
- **clustering_algorithm**: 0.0% complete (27 null values)
- **algorithm_parameters**: 0.0% complete (27 null values)
- **quality_validation_date**: 0.0% complete (27 null values)
- **business_review_date**: 0.0% complete (27 null values)
- **created_timestamp**: 100% complete

**Data Quality - Duplicates:**

- ✅ No duplicate records found

**Sample Data by Column:**

- **cluster_id**: `0`, `1`, `2`, `3`, `4`, `5`, `6`, `7`, `8`, `9`
- **bundle_name**: `Administration Skills Bundl...`, `Analysis Skills Bundle (91 ...`, `Architecture and Constructi...`, `Business Skills Bundle (434...`, `Customer and Client Support...`, `Design Skills Bundle (42 sk...`, `Economics, Policy, and Soci...`, `Education and Training Skil...`, `Engineering Skills Bundle (...`, `Environment Skills Bundle (...`
- **bundle_description**: `Collection of Administratio...`, `Collection of Analysis skil...`, `Collection of Architecture ...`, `Collection of Business skil...`, `Collection of Customer and ...`, `Collection of Design skills...`, `Collection of Economics, Po...`, `Collection of Education and...`, `Collection of Engineering s...`, `Collection of Environment s...`
- **bundle_rationale**: `Grouped by Administration c...`, `Grouped by Analysis category`, `Grouped by Architecture and...`, `Grouped by Business category`, `Grouped by Customer and Cli...`, `Grouped by Design category`, `Grouped by Economics, Polic...`, `Grouped by Education and Tr...`, `Grouped by Engineering cate...`, `Grouped by Environment cate...`
- **bundle_size**: `3`, `7`, `9`, `11`, `14`, `19`, `20`, `21`, `22`, `23`
- **sample_skills**: `Catering Management; Cateri...`, `Customer Advocacy; Customer...`, `Customer Centricity; Data A...`, `Customer Retention; Custome...`, `Employee Coaching; Employee...`, `Environmental Risk Assessme...`, `Financial Modeling; Financi...`, `Goal Setting; Customer Insi...`, `IT Security Documentation; ...`, `Influencing Skills; Emotion...`
- **sample_job_functions**: `Analysis pending`
- **dominant_category**: `Administration`, `Analysis`, `Architecture and Construction`, `Business`, `Customer and Client Support`, `Design`, `Economics, Policy, and Soci...`, `Education and Training`, `Engineering`, `Environment`
- **category_purity**: `1.0`
- **application_level**: `Advanced`
- **specialization_area**: `Administration`, `Analysis`, `Architecture and Construction`, `Business`, `Customer and Client Support`, `Design`, `Economics, Policy, and Soci...`, `Education and Training`, `Engineering`, `Environment`
- **average_jobs_per_skill**: `3.0`, `3.1818181818181817`, `3.838709677419355`, `3.9523809523809526`, `4.142857142857143`, `4.666666666666667`, `5.090909090909091`, `5.928571428571429`, `6.25`, `7.0`
- **taxonomy_alignment_score**: `0.8`
- **silhouette_score**: `0.0`
- **created_timestamp**: `2025-08-08T13:51:05.605307`, `2025-08-08T13:51:05.640235`, `2025-08-08T13:51:05.644039`, `2025-08-08T13:51:05.648056`, `2025-08-08T13:51:05.655172`, `2025-08-08T13:51:05.657177`, `2025-08-08T13:51:05.660239`, `2025-08-08T13:51:05.700562`, `2025-08-08T13:51:05.707836`, `2025-08-08T13:51:05.710443`

**Sample Complete Records:**

**Record 1:**
  - `cluster_id`: 0
  - `bundle_name`: Analysis Skills Bundle (91 skills)
  - `bundle_description`: Collection of Analysis skills with 3.1% average...
  - `bundle_rationale`: Grouped by Analysis category
  - `bundle_size`: 91
  - `sample_skills`: Customer Centricity; Data Analysis; Data Literacy
  - `sample_job_functions`: Analysis pending
  - `dominant_category`: Analysis
  - `category_purity`: 1.0
  - `application_level`: Advanced
  - `specialization_area`: Analysis
  - `average_jobs_per_skill`: 22.428571428571427
  - `taxonomy_alignment_score`: 0.8
  - `silhouette_score`: 0.0
  - `created_timestamp`: 2025-08-08T13:51:05.605307

**Record 2:**
  - `cluster_id`: 1
  - `bundle_name`: Business Skills Bundle (434 skills)
  - `bundle_description`: Collection of Business skills with 5.2% average...
  - `bundle_rationale`: Grouped by Business category
  - `bundle_size`: 434
  - `sample_skills`: Stakeholder Engagement; Change Management; Cons...
  - `sample_job_functions`: Analysis pending
  - `dominant_category`: Business
  - `category_purity`: 1.0
  - `application_level`: Advanced
  - `specialization_area`: Business
  - `average_jobs_per_skill`: 36.86405529953917
  - `taxonomy_alignment_score`: 0.8
  - `silhouette_score`: 0.0
  - `created_timestamp`: 2025-08-08T13:51:05.640235

**Record 3:**
  - `cluster_id`: 2
  - `bundle_name`: Media and Communications Skills Bundle (59 skills)
  - `bundle_description`: Collection of Media and Communications skills w...
  - `bundle_rationale`: Grouped by Media and Communications category
  - `bundle_size`: 59
  - `sample_skills`: Strategic Communication; Technical Report; Effe...
  - `sample_job_functions`: Analysis pending
  - `dominant_category`: Media and Communications
  - `category_purity`: 1.0
  - `application_level`: Advanced
  - `specialization_area`: Media and Communications
  - `average_jobs_per_skill`: 33.186440677966104
  - `taxonomy_alignment_score`: 0.8
  - `silhouette_score`: 0.0
  - `created_timestamp`: 2025-08-08T13:51:05.644039

---

### 2. **analytics_job_defining_skills** - 19,460 records

```sql
CREATE TABLE analytics_job_defining_skills (
    job_profile_id TEXT PRIMARY KEY,
    skill_id TEXT PRIMARY KEY,
    skill_name TEXT,
    job_profile TEXT,
    category TEXT,
    subcategory TEXT,
    skill_type TEXT,
    prevalence_percentage REAL,
    total_profiles_with_skill INTEGER,
    rarity_category TEXT,
    defining_skill_rank INTEGER,
    defining_skill_score REAL,
    analysis_date TEXT,
    percentile_threshold REAL,
    created_timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);
```

**Foreign Key Relationships:**

- `skill_id` â†’ `core_skills_taxonomy.Skill_ID`
- `job_profile_id` â†’ `core_job_architecture.JobProfileID`

**Column Statistics:**

- **job_profile_id**: 715 unique values (19,460 non-null), avg length 7.0
- **skill_id**: 2,034 unique values (19,460 non-null), avg length 20.0
- **skill_name**: 2,034 unique values (19,460 non-null), avg length 21.53
- **job_profile**: 309 unique values (19,460 non-null), avg length 22.46
- **category**: 29 unique values (19,460 non-null), avg length 16.21
- **subcategory**: 241 unique values (19,460 non-null), avg length 20.41
- **skill_type**: 3 unique values (19,460 non-null), avg length 16.6
- **prevalence_percentage**: 108 unique values (19,460 non-null), range 0.1400 - 89.7900, avg 3.6839
- **total_profiles_with_skill**: 108 unique values (19,460 non-null), range 1 - 642
- **rarity_category**: 4 unique values (19,460 non-null), avg length 5.12
- **defining_skill_rank**: 47 unique values (19,460 non-null), range 1 - 47
- **defining_skill_score**: 108 unique values (19,460 non-null), range 10.2098 - 99.8601, avg 96.3167
- **analysis_date**: 1 unique values (19,460 non-null), avg length 10.0
- **percentile_threshold**: 1 unique values (19,460 non-null), range 8.8000 - 8.8000, avg 8.8000
- **created_timestamp**: 1 unique values (19,460 non-null), avg length 19.0

**Data Quality - Completeness:**

- **job_profile_id**: 100% complete
- **skill_id**: 100% complete
- **skill_name**: 100% complete
- **job_profile**: 100% complete
- **category**: 100% complete
- **subcategory**: 100% complete
- **skill_type**: 100% complete
- **prevalence_percentage**: 100% complete
- **total_profiles_with_skill**: 100% complete
- **rarity_category**: 100% complete
- **defining_skill_rank**: 100% complete
- **defining_skill_score**: 100% complete
- **analysis_date**: 100% complete
- **percentile_threshold**: 100% complete
- **created_timestamp**: 100% complete

**Data Quality - Duplicates:**

- ✅ No duplicate records found

**Sample Data by Column:**

- **job_profile_id**: `R0001.5`, `R0001.6`, `R0002.0`, `R0002.1`, `R0002.2`, `R0002.3`, `R0002.4`, `R0003.0`, `R0003.2`, `R0005.1`
- **skill_id**: `BGS10EE289B9FDE2C4B1`, `BGS11665AC6BD06C5EBD`, `BGS117E3FE9519A5B542`, `BGS1241B6719A7FE041D`, `BGS1250D82C4B027A171`, `BGS147DBB4CF132F0523`, `BGS152BE1A314EFF3FE3`, `BGS166A638195D1E2BAE`, `BGS16C952D775A16E650`, `BGS1737E89A3E6B7A57C`
- **skill_name**: `A3 Problem Solving Techniques`, `ADP Enterprise`, `AWS Certified DevOps Engineer`, `AWS Devops`, `AWS Identity And Access Man...`, `Access Controls`, `Account Development`, `Account Growth`, `Account Management`, `Account Reconciliation`
- **job_profile**: `Budget Manager (Ungraded)`, `Budget Manager - 0`, `Budget Manager - 2`, `Budget Manager - 3`, `Budget Manager - 4`, `Budget Manager - 5`, `Budget Manager - 6`, `Budget Manager - 7`, `Budget Manager - II`, `Business Analyst - 0`
- **category**: `Administration`, `Analysis`, `Architecture and Construction`, `Business`, `Customer and Client Support`, `Design`, `Economics, Policy, and Soci...`, `Education and Training`, `Energy and Utilities`, `Engineering`
- **subcategory**: `Account Management`, `Accounting and Finance Soft...`, `Accounts Payable and Receiv...`, `Administrative Support and ...`, `Agile Software Development`, `Animation and Game Design`, `Application Programming Int...`, `Architectural Design`, `Artificial Intelligence and...`, `Auditing`
- **skill_type**: `Certification`, `Common Skill`, `Specialized Skill`
- **prevalence_percentage**: `0.14`, `0.28`, `0.42`, `0.56`, `0.7`, `0.84`, `0.98`, `1.12`, `1.26`, `1.4`
- **total_profiles_with_skill**: `1`, `2`, `3`, `4`, `5`, `6`, `7`, `8`, `9`, `10`
- **rarity_category**: `Common`, `Rare`, `Uncommon`, `Universal`
- **defining_skill_rank**: `1`, `2`, `3`, `4`, `5`, `6`, `7`, `8`, `9`, `10`
- **defining_skill_score**: `10.209790209790214`, `54.68531468531469`, `68.39160839160839`, `70.06993006993007`, `70.34965034965035`, `71.32867132867133`, `76.5034965034965`, `76.92307692307692`, `77.9020979020979`, `79.72027972027972`
- **analysis_date**: `2025-08-07`
- **percentile_threshold**: `8.8`
- **created_timestamp**: `2025-08-07 02:14:35`

**Sample Complete Records:**

**Record 1:**
  - `job_profile_id`: R0001.5
  - `skill_id`: KS1215K6H2C5BNN63SHB
  - `skill_name`: Infor LX
  - `job_profile`: Payment Systems Analyst - 5
  - `category`: Business
  - `subcategory`: Business Operations
  - `skill_type`: Specialized Skill
  - `prevalence_percentage`: 1.96
  - `total_profiles_with_skill`: 14
  - `rarity_category`: Rare
  - `defining_skill_rank`: 18
  - `defining_skill_score`: 98.04195804195804
  - `analysis_date`: 2025-08-07
  - `percentile_threshold`: 8.8
  - `created_timestamp`: 2025-08-07 02:14:35

**Record 2:**
  - `job_profile_id`: R0001.5
  - `skill_id`: KS441036Q8YQ0P81GPB0
  - `skill_name`: Strategic Partnership
  - `job_profile`: Payment Systems Analyst - 5
  - `category`: Business
  - `subcategory`: Business Strategy
  - `skill_type`: Specialized Skill
  - `prevalence_percentage`: 3.22
  - `total_profiles_with_skill`: 23
  - `rarity_category`: Rare
  - `defining_skill_rank`: 25
  - `defining_skill_score`: 96.78321678321679
  - `analysis_date`: 2025-08-07
  - `percentile_threshold`: 8.8
  - `created_timestamp`: 2025-08-07 02:14:35

**Record 3:**
  - `job_profile_id`: R0001.5
  - `skill_id`: ESED90D9CF0E0C9F8D28
  - `skill_name`: Business Advisory
  - `job_profile`: Payment Systems Analyst - 5
  - `category`: Business
  - `subcategory`: Business Strategy
  - `skill_type`: Specialized Skill
  - `prevalence_percentage`: 2.24
  - `total_profiles_with_skill`: 16
  - `rarity_category`: Rare
  - `defining_skill_rank`: 20
  - `defining_skill_score`: 97.76223776223776
  - `analysis_date`: 2025-08-07
  - `percentile_threshold`: 8.8
  - `created_timestamp`: 2025-08-07 02:14:35

---

### 3. **analytics_job_families** - 715 records

```sql
CREATE TABLE analytics_job_families (
    job_profile_id TEXT PRIMARY KEY,
    job_profile TEXT,
    job_function TEXT,
    job_sub_function TEXT,
    job_category TEXT,
    management_level TEXT,
    cluster_id INTEGER PRIMARY KEY,
    cluster_name TEXT,
    cluster_description TEXT,
    cluster_rationale TEXT,
    cluster_size INTEGER,
    sample_jobs TEXT,
    sample_skills TEXT,
    cluster_confidence REAL,
    silhouette_score REAL,
    intra_cluster_similarity REAL,
    inter_cluster_distance REAL,
    clustering_algorithm TEXT,
    algorithm_parameters TEXT,
    analysis_date TEXT,
    created_timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);
```

**Foreign Key Relationships:**

- `job_profile_id` â†’ `core_job_architecture.JobProfileID`

**Column Statistics:**

- **job_profile_id**: 715 unique values (715 non-null), avg length 7.0
- **job_profile**: 309 unique values (715 non-null), avg length 22.48
- **job_function**: 22 unique values (715 non-null), avg length 19.57
- **job_sub_function**: 110 unique values (715 non-null), avg length 17.58
- **job_category**: 4 unique values (715 non-null), avg length 10.87
- **management_level**: 8 unique values (715 non-null), avg length 7.02
- **cluster_id**: 18 unique values (715 non-null), range 0 - 17
- **cluster_name**: 13 unique values (715 non-null), avg length 39.98
- **cluster_description**: 18 unique values (715 non-null), avg length 78.1
- **cluster_rationale**: 1 unique values (715 non-null), avg length 86.0
- **cluster_size**: 16 unique values (715 non-null), range 5 - 116
- **sample_jobs**: 18 unique values (715 non-null), avg length 75.78
- **sample_skills**: 1 unique values (715 non-null), avg length 23.0
- **cluster_confidence**: 2 unique values (715 non-null), range 0.1270 - 0.1390, avg 0.1387
- **silhouette_score**: 1 unique values (715 non-null), range 0.1157 - 0.1157, avg 0.1157
- **intra_cluster_similarity**: 1 unique values (715 non-null), range 0.0000 - 0.0000, avg 0.0000
- **inter_cluster_distance**: 1 unique values (715 non-null), range 0.0000 - 0.0000, avg 0.0000
- **clustering_algorithm**: 1 unique values (715 non-null), avg length 6.0
- **algorithm_parameters**: 1 unique values (715 non-null), avg length 30.0
- **analysis_date**: 1 unique values (715 non-null), avg length 10.0
- **created_timestamp**: 1 unique values (715 non-null), avg length 26.0

**Data Quality - Completeness:**

- **job_profile_id**: 100% complete
- **job_profile**: 100% complete
- **job_function**: 100% complete
- **job_sub_function**: 100% complete
- **job_category**: 100% complete
- **management_level**: 100% complete
- **cluster_id**: 100% complete
- **cluster_name**: 100% complete
- **cluster_description**: 100% complete
- **cluster_rationale**: 100% complete
- **cluster_size**: 100% complete
- **sample_jobs**: 100% complete
- **sample_skills**: 100% complete
- **cluster_confidence**: 100% complete
- **silhouette_score**: 100% complete
- **intra_cluster_similarity**: 100% complete
- **inter_cluster_distance**: 100% complete
- **clustering_algorithm**: 100% complete
- **algorithm_parameters**: 100% complete
- **analysis_date**: 100% complete
- **created_timestamp**: 100% complete

**Data Quality - Duplicates:**

- ✅ No duplicate records found

**Sample Data by Column:**

- **job_profile_id**: `R0001.5`, `R0001.6`, `R0002.0`, `R0002.1`, `R0002.2`, `R0002.3`, `R0002.4`, `R0003.0`, `R0003.2`, `R0005.1`
- **job_profile**: `Budget Manager (Ungraded)`, `Budget Manager - 0`, `Budget Manager - 2`, `Budget Manager - 3`, `Budget Manager - 4`, `Budget Manager - 5`, `Budget Manager - 6`, `Budget Manager - 7`, `Budget Manager - II`, `Business Analyst - 0`
- **job_function**: `Audit & Assurance`, `Banking Services`, `Business Development`, `Customer Relations`, `Data & Analytics`, `Executive Leadership`, `Facilities & Administration`, `Finance & Treasury`, `Human Resources`, `Investment Management`
- **job_sub_function**: `Account Management`, `Actuarial Services`, `Anti-Money Laundering`, `Application Support`, `Artificial Intelligence`, `Asset Management`, `Audit & Assurance`, `Basel Compliance`, `Brand Management`, `Budgeting & Forecasting`
- **job_category**: `Enabling`, `Executive & General Management`, `Revenue Generating`, `Support`
- **management_level**: `Group 1`, `Group 2`, `Group 3`, `Group 4`, `Group 5`, `Group 6`, `Group 7`, `Group NA`
- **cluster_id**: `0`, `1`, `2`, `3`, `4`, `5`, `6`, `7`, `8`, `9`
- **cluster_name**: `Banking Services - Group 2 ...`, `Banking Services - Group 3 ...`, `Data & Analytics - Group 2 ...`, `Facilities & Administration...`, `Facilities & Administration...`, `Finance & Treasury - Group ...`, `Finance & Treasury - Group ...`, `Investment Management - Gro...`, `Investment Management - Gro...`, `Marketing & Communications ...`
- **cluster_description**: `Diverse cluster of 10 roles...`, `Diverse cluster of 116 role...`, `Diverse cluster of 12 roles...`, `Diverse cluster of 22 roles...`, `Diverse cluster of 25 roles...`, `Diverse cluster of 36 roles...`, `Diverse cluster of 36 roles...`, `Diverse cluster of 38 roles...`, `Diverse cluster of 39 roles...`, `Diverse cluster of 42 roles...`
- **cluster_rationale**: `Clustered based on cross-fu...`
- **cluster_size**: `5`, `6`, `10`, `12`, `22`, `25`, `36`, `38`, `39`, `42`
- **sample_jobs**: `Business Analyst - I; Legal...`, `Business Banker - 2; Sales ...`, `Cloud Architect - 0; Digita...`, `Compliance Officer - 0; Cre...`, `Compliance Officer - 7; Clo...`, `Credit Risk Manager - 7; Pr...`, `Financial Analyst - III; Fi...`, `Operational Risk Specialist...`, `Operations Analyst - 0; Ope...`, `Payment Systems Analyst - 5...`
- **sample_skills**: `Skills analysis pending`
- **cluster_confidence**: `0.127`, `0.139`
- **silhouette_score**: `0.11569655786645812`
- **intra_cluster_similarity**: `0.0`
- **inter_cluster_distance**: `0.0`
- **clustering_algorithm**: `KMEANS`
- **algorithm_parameters**: `n_clusters=18, random_state=42`
- **analysis_date**: `2025-08-08`
- **created_timestamp**: `2025-08-08T13:51:05.434547`

**Sample Complete Records:**

**Record 1:**
  - `job_profile_id`: R0001.5
  - `job_profile`: Payment Systems Analyst - 5
  - `job_function`: Data & Analytics
  - `job_sub_function`: Data Governance
  - `job_category`: Support
  - `management_level`: Group 2
  - `cluster_id`: 17
  - `cluster_name`: Facilities & Administration - Group 2 Cluster
  - `cluster_description`: Diverse cluster of 75 roles spanning 21 job fun...
  - `cluster_rationale`: Clustered based on cross-functional skill simil...
  - `cluster_size`: 75
  - `sample_jobs`: Payment Systems Analyst - 5; Settlement Officer...
  - `sample_skills`: Skills analysis pending
  - `cluster_confidence`: 0.139
  - `silhouette_score`: 0.11569655786645812
  - `intra_cluster_similarity`: 0.0
  - `inter_cluster_distance`: 0.0
  - `clustering_algorithm`: KMEANS
  - `algorithm_parameters`: n_clusters=18, random_state=42
  - `analysis_date`: 2025-08-08
  - `created_timestamp`: 2025-08-08T13:51:05.434547

**Record 2:**
  - `job_profile_id`: R0001.6
  - `job_profile`: Settlement Officer - 6
  - `job_function`: Data & Analytics
  - `job_sub_function`: Machine Learning
  - `job_category`: Support
  - `management_level`: Group 1
  - `cluster_id`: 17
  - `cluster_name`: Facilities & Administration - Group 2 Cluster
  - `cluster_description`: Diverse cluster of 75 roles spanning 21 job fun...
  - `cluster_rationale`: Clustered based on cross-functional skill simil...
  - `cluster_size`: 75
  - `sample_jobs`: Payment Systems Analyst - 5; Settlement Officer...
  - `sample_skills`: Skills analysis pending
  - `cluster_confidence`: 0.139
  - `silhouette_score`: 0.11569655786645812
  - `intra_cluster_similarity`: 0.0
  - `inter_cluster_distance`: 0.0
  - `clustering_algorithm`: KMEANS
  - `algorithm_parameters`: n_clusters=18, random_state=42
  - `analysis_date`: 2025-08-08
  - `created_timestamp`: 2025-08-08T13:51:05.434547

**Record 3:**
  - `job_profile_id`: R0002.0
  - `job_profile`: Sales Manager - II
  - `job_function`: Banking Services
  - `job_sub_function`: Investment Banking
  - `job_category`: Enabling
  - `management_level`: Group 4
  - `cluster_id`: 9
  - `cluster_name`: Operations & Processing - Group 2 Cluster
  - `cluster_description`: Diverse cluster of 93 roles spanning 21 job fun...
  - `cluster_rationale`: Clustered based on cross-functional skill simil...
  - `cluster_size`: 93
  - `sample_jobs`: Sales Manager - II; Sales Manager - 1; Relation...
  - `sample_skills`: Skills analysis pending
  - `cluster_confidence`: 0.139
  - `silhouette_score`: 0.11569655786645812
  - `intra_cluster_similarity`: 0.0
  - `inter_cluster_distance`: 0.0
  - `clustering_algorithm`: KMEANS
  - `algorithm_parameters`: n_clusters=18, random_state=42
  - `analysis_date`: 2025-08-08
  - `created_timestamp`: 2025-08-08T13:51:05.434547

---

### 4. **analytics_job_similarities** - 510,510 records

```sql
CREATE TABLE analytics_job_similarities (
    similarity_id TEXT PRIMARY KEY,
    job_from TEXT,
    job_to TEXT,
    similarity_score REAL,
    enhanced_similarity_score REAL,
    rarity_weighted_score REAL,
    shared_defining_skills_count INTEGER,
    defining_skill_boost REAL,
    shared_skills_count INTEGER,
    total_skills_from INTEGER,
    total_skills_to INTEGER,
    skill_overlap_percentage REAL,
    shared_skills TEXT,
    shared_defining_skills TEXT,
    skill_gap_analysis TEXT,
    calculation_algorithm TEXT,
    created_timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);
```

**Foreign Key Relationships:**

- `job_to` â†’ `core_job_architecture.JobProfileID`
- `job_from` â†’ `core_job_architecture.JobProfileID`

**Column Statistics:**

- **similarity_id**: 510,510 unique values (510,510 non-null), avg length 15.0
- **job_from**: 715 unique values (510,510 non-null), avg length 7.0
- **job_to**: 715 unique values (510,510 non-null), avg length 7.0
- **similarity_score**: 1,981 unique values (510,510 non-null), range 0.0000 - 1.0000, avg 0.0004
- **enhanced_similarity_score**: 1,981 unique values (510,510 non-null), range 0.0000 - 4501.5850, avg 1.6140
- **rarity_weighted_score**: 1,981 unique values (510,510 non-null), range 0.0000 - 4501.5850, avg 1.6140
- **shared_defining_skills_count**: 41 unique values (510,510 non-null), range 0 - 47
- **defining_skill_boost**: 3,052 unique values (510,510 non-null), range 0.0000 - 4500.5849, avg 1.2713
- **shared_skills_count**: 80 unique values (510,510 non-null), range 0 - 96
- **total_skills_from**: 53 unique values (510,510 non-null), range 23 - 96
- **total_skills_to**: 53 unique values (510,510 non-null), range 23 - 96
- **skill_overlap_percentage**: 637 unique values (510,510 non-null), range 0.0000 - 100.0000, avg 34.2701
- **shared_skills**: 6,155 unique values (510,510 non-null), avg length 174.98
- **shared_defining_skills**: 6,464 unique values (510,510 non-null), avg length 27.89
- **skill_gap_analysis**: 881 unique values (510,510 non-null), avg length 35.99
- **calculation_algorithm**: 1 unique values (510,510 non-null), avg length 20.0
- **created_timestamp**: 18 unique values (510,510 non-null), avg length 19.0

**Data Quality - Completeness:**

- **similarity_id**: 100% complete
- **job_from**: 100% complete
- **job_to**: 100% complete
- **similarity_score**: 100% complete
- **enhanced_similarity_score**: 100% complete
- **rarity_weighted_score**: 100% complete
- **shared_defining_skills_count**: 100% complete
- **defining_skill_boost**: 100% complete
- **shared_skills_count**: 100% complete
- **total_skills_from**: 100% complete
- **total_skills_to**: 100% complete
- **skill_overlap_percentage**: 100% complete
- **shared_skills**: 100% complete
- **shared_defining_skills**: 100% complete
- **skill_gap_analysis**: 100% complete
- **calculation_algorithm**: 100% complete
- **created_timestamp**: 100% complete

**Data Quality - Duplicates:**

- ✅ No duplicate records found

**Sample Data by Column:**

- **similarity_id**: `R0001.5_R0001.6`, `R0001.5_R0002.0`, `R0001.5_R0002.1`, `R0001.5_R0002.2`, `R0001.5_R0002.3`, `R0001.5_R0002.4`, `R0001.5_R0003.0`, `R0001.5_R0003.2`, `R0001.5_R0005.1`, `R0001.5_R0007.1`
- **job_from**: `R0001.5`, `R0001.6`, `R0002.0`, `R0002.1`, `R0002.2`, `R0002.3`, `R0002.4`, `R0003.0`, `R0003.2`, `R0005.1`
- **job_to**: `R0001.5`, `R0001.6`, `R0002.0`, `R0002.1`, `R0002.2`, `R0002.3`, `R0002.4`, `R0003.0`, `R0003.2`, `R0005.1`
- **similarity_score**: `0.0`, `2.2214397817657557e-06`, `2.4435837599423316e-06`, `2.665727738118907e-06`, `2.887871716295483e-06`, `3.1100156944720577e-06`, `3.3321596726486336e-06`, `3.5543036508252095e-06`, `3.776447629001785e-06`, `3.998591607178361e-06`
- **enhanced_similarity_score**: `0.0`, `0.01`, `0.011000000000000001`, `0.012`, `0.013000000000000001`, `0.013999999999999999`, `0.015`, `0.016`, `0.017`, `0.018000000000000002`
- **rarity_weighted_score**: `0.0`, `0.01`, `0.011000000000000001`, `0.012`, `0.013000000000000001`, `0.013999999999999999`, `0.015`, `0.016`, `0.017`, `0.018000000000000002`
- **shared_defining_skills_count**: `0`, `1`, `2`, `3`, `4`, `5`, `6`, `7`, `8`, `9`
- **defining_skill_boost**: `0.0`, `0.0024`, `0.0028`, `0.0029`, `0.003`, `0.0031`, `0.0032`, `0.0033`, `0.0034`, `0.0035`
- **shared_skills_count**: `0`, `1`, `2`, `3`, `4`, `5`, `6`, `7`, `8`, `9`
- **total_skills_from**: `23`, `25`, `26`, `27`, `31`, `32`, `33`, `34`, `36`, `37`
- **total_skills_to**: `23`, `25`, `26`, `27`, `31`, `32`, `33`, `34`, `36`, `37`
- **skill_overlap_percentage**: `0.0`, `1.0`, `1.1`, `1.2`, `1.3`, `1.4`, `1.5`, `1.6`, `1.7`, `1.8`
- **shared_skills**: ``, `A3 Problem Solving Techniqu...`, `Account Reconciliation, Dat...`, `Account Reconciliation, Ris...`, `Account Reconciliation, Ris...`, `Account Reconciliation, Ris...`, `Active Listening`, `Active Listening, Problem S...`, `Agile Coaching, Cross-Funct...`, `Agile Coaching, Project Por...`
- **shared_defining_skills**: ``, `A3 Problem Solving Techniques`, `A3 Problem Solving Techniqu...`, `Account Growth, Business Re...`, `Account Reconciliation, Cus...`, `Account Reconciliation, Dat...`, `Account Reconciliation, Fin...`, `Account Reconciliation, Fin...`, `Accounting Information Syst...`, `Active Listening`
- **skill_gap_analysis**: `Skills needed: 0, Defining ...`, `Skills needed: 10, Defining...`, `Skills needed: 10, Defining...`, `Skills needed: 10, Defining...`, `Skills needed: 10, Defining...`, `Skills needed: 10, Defining...`, `Skills needed: 11, Defining...`, `Skills needed: 11, Defining...`, `Skills needed: 11, Defining...`, `Skills needed: 11, Defining...`
- **calculation_algorithm**: `rarity_weighted_v1.0`
- **created_timestamp**: `2025-08-07 02:14:17`, `2025-08-07 02:14:18`, `2025-08-07 02:14:19`, `2025-08-07 02:14:20`, `2025-08-07 02:14:21`, `2025-08-07 02:14:22`, `2025-08-07 02:14:23`, `2025-08-07 02:14:24`, `2025-08-07 02:14:25`, `2025-08-07 02:14:26`

**Sample Complete Records:**

**Record 1:**
  - `similarity_id`: R0001.5_R0001.6
  - `job_from`: R0001.5
  - `job_to`: R0001.6
  - `similarity_score`: 0.08161369828627027
  - `enhanced_similarity_score`: 367.39099999999996
  - `rarity_weighted_score`: 367.39099999999996
  - `shared_defining_skills_count`: 33
  - `defining_skill_boost`: 366.3914
  - `shared_skills_count`: 68
  - `total_skills_from`: 68
  - `total_skills_to`: 68
  - `skill_overlap_percentage`: 100.0
  - `shared_skills`: Infor LX, Safety Culture, Strategic Partnership...
  - `shared_defining_skills`: Infor LX, Strategic Partnership, Business Advis...
  - `skill_gap_analysis`: Skills needed: 0, Defining gaps: 0
  - `calculation_algorithm`: rarity_weighted_v1.0
  - `created_timestamp`: 2025-08-07 02:14:17

**Record 2:**
  - `similarity_id`: R0001.5_R0002.0
  - `job_from`: R0001.5
  - `job_to`: R0002.0
  - `similarity_score`: 0.00016038795224348757
  - `enhanced_similarity_score`: 0.722
  - `rarity_weighted_score`: 0.722
  - `shared_defining_skills_count`: 4
  - `defining_skill_boost`: 0.3692
  - `shared_skills_count`: 24
  - `total_skills_from`: 68
  - `total_skills_to`: 49
  - `skill_overlap_percentage`: 49.0
  - `shared_skills`: Safety Culture, Business Acumen, Vision Develop...
  - `shared_defining_skills`: Business Acumen, Business Administration, Power...
  - `skill_gap_analysis`: Skills needed: 25, Defining gaps: 20
  - `calculation_algorithm`: rarity_weighted_v1.0
  - `created_timestamp`: 2025-08-07 02:14:17

**Record 3:**
  - `similarity_id`: R0001.5_R0002.1
  - `job_from`: R0001.5
  - `job_to`: R0002.1
  - `similarity_score`: 0.00016038795224348757
  - `enhanced_similarity_score`: 0.722
  - `rarity_weighted_score`: 0.722
  - `shared_defining_skills_count`: 4
  - `defining_skill_boost`: 0.3692
  - `shared_skills_count`: 24
  - `total_skills_from`: 68
  - `total_skills_to`: 49
  - `skill_overlap_percentage`: 49.0
  - `shared_skills`: Safety Culture, Business Acumen, Vision Develop...
  - `shared_defining_skills`: Business Acumen, Business Administration, Power...
  - `skill_gap_analysis`: Skills needed: 25, Defining gaps: 20
  - `calculation_algorithm`: rarity_weighted_v1.0
  - `created_timestamp`: 2025-08-07 02:14:17

---

### 5. **analytics_movement_patterns** - 25,608 records

```sql
CREATE TABLE analytics_movement_patterns (
    movement_pattern_id TEXT PRIMARY KEY,
    movement_month TEXT,
    from_position TEXT,
    to_position TEXT,
    from_job_profile_id TEXT,
    to_job_profile_id TEXT,
    movement_count INTEGER,
    unique_employees INTEGER,
    avg_days_between REAL,
    pct_total_movements REAL,
    movement_type TEXT,
    skill_similarity_score REAL,
    difficulty_score REAL,
    success_rate REAL,
    created_timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);
```

**Foreign Key Relationships:**

- `to_job_profile_id` â†’ `core_job_architecture.JobProfileID`
- `from_job_profile_id` â†’ `core_job_architecture.JobProfileID`

**Column Statistics:**

- **movement_pattern_id**: 25,608 unique values (25,608 non-null), avg length 14.0
- **movement_month**: 49 unique values (25,608 non-null), avg length 7.0
- **from_position**: 4,935 unique values (25,608 non-null), avg length 8.35
- **to_position**: 4,938 unique values (25,608 non-null), avg length 8.35
- **from_job_profile_id**: 620 unique values (23,356 non-null), avg length 7.0
- **to_job_profile_id**: 620 unique values (23,342 non-null), avg length 7.0
- **movement_count**: 4 unique values (25,608 non-null), range 1 - 4
- **unique_employees**: 1 unique values (25,608 non-null), range 1 - 1
- **avg_days_between**: 93 unique values (25,608 non-null), range 0.0000 - 364.0000, avg 92.6085
- **pct_total_movements**: 55 unique values (25,608 non-null), range 0.0800 - 10.0000, avg 0.1909
- **movement_type**: 1 unique values (25,608 non-null), avg length 7.0
- **skill_similarity_score**: 0 unique values (0 non-null), range 0.0000 - 0.0000, avg 0.0000
- **difficulty_score**: 0 unique values (0 non-null), range 0.0000 - 0.0000, avg 0.0000
- **success_rate**: 0 unique values (0 non-null), range 0.0000 - 0.0000, avg 0.0000
- **created_timestamp**: 94 unique values (25,608 non-null), avg length 26.0

**Data Quality - Completeness:**

- **movement_pattern_id**: 100% complete
- **movement_month**: 100% complete
- **from_position**: 100% complete
- **to_position**: 100% complete
- **from_job_profile_id**: 91.21% complete (2,252 null values)
- **to_job_profile_id**: 91.15% complete (2,266 null values)
- **movement_count**: 100% complete
- **unique_employees**: 100% complete
- **avg_days_between**: 100% complete
- **pct_total_movements**: 100% complete
- **movement_type**: 100% complete
- **skill_similarity_score**: 0.0% complete (25,608 null values)
- **difficulty_score**: 0.0% complete (25,608 null values)
- **success_rate**: 0.0% complete (25,608 null values)
- **created_timestamp**: 100% complete

**Data Quality - Duplicates:**

- ✅ No duplicate records found

**Sample Data by Column:**

- **movement_pattern_id**: `pattern_000001`, `pattern_000002`, `pattern_000003`, `pattern_000004`, `pattern_000005`, `pattern_000006`, `pattern_000007`, `pattern_000008`, `pattern_000009`, `pattern_000010`
- **movement_month**: `2021-07`, `2021-08`, `2021-09`, `2021-10`, `2021-11`, `2021-12`, `2022-01`, `2022-02`, `2022-03`, `2022-04`
- **from_position**: `100611478735`, `101205286900`, `101223857343`, `101345305549`, `101520465603`, `101619593152`, `102032128040`, `102557168899`, `103170005904`, `103189149165`
- **to_position**: `100611478735`, `101205286900`, `101223857343`, `101345305549`, `101520465603`, `101619593152`, `102032128040`, `102557168899`, `103170005904`, `103189149165`
- **from_job_profile_id**: `R0001.5`, `R0001.6`, `R0002.0`, `R0002.1`, `R0002.2`, `R0003.0`, `R0003.2`, `R0005.1`, `R0009.0`, `R0009.1`
- **to_job_profile_id**: `R0001.5`, `R0001.6`, `R0002.0`, `R0002.1`, `R0002.2`, `R0003.0`, `R0003.2`, `R0005.1`, `R0009.0`, `R0009.1`
- **movement_count**: `1`, `2`, `3`, `4`
- **unique_employees**: `1`
- **avg_days_between**: `0.0`, `7.0`, `14.0`, `21.0`, `28.0`, `35.0`, `38.5`, `42.0`, `49.0`, `56.0`
- **pct_total_movements**: `0.08`, `0.09`, `0.1`, `0.11`, `0.13`, `0.14`, `0.16`, `0.17`, `0.18`, `0.19`
- **movement_type**: `lateral`
- **created_timestamp**: `2025-08-07T10:15:33.484367`, `2025-08-07T10:15:33.500365`, `2025-08-07T10:15:33.504287`, `2025-08-07T10:15:33.506293`, `2025-08-07T10:15:33.516118`, `2025-08-07T10:15:33.517977`, `2025-08-07T10:15:33.531884`, `2025-08-07T10:15:33.547724`, `2025-08-07T10:15:33.563672`, `2025-08-07T10:15:33.578383`

**Sample Complete Records:**

**Record 1:**
  - `movement_pattern_id`: pattern_001121
  - `movement_month`: 2021-07
  - `from_position`: 50002954
  - `to_position`: 50002822
  - `from_job_profile_id`: R0264.6
  - `to_job_profile_id`: R0238.0
  - `movement_count`: 3
  - `unique_employees`: 1
  - `avg_days_between`: 0.0
  - `pct_total_movements`: 0.25
  - `movement_type`: lateral
  - `created_timestamp`: 2025-08-07T10:15:33.484367

**Record 2:**
  - `movement_pattern_id`: pattern_001530
  - `movement_month`: 2021-07
  - `from_position`: 146534508928
  - `to_position`: 50003796
  - `to_job_profile_id`: R0280.2
  - `movement_count`: 3
  - `unique_employees`: 1
  - `avg_days_between`: 0.0
  - `pct_total_movements`: 0.25
  - `movement_type`: lateral
  - `created_timestamp`: 2025-08-07T10:15:33.484367

**Record 3:**
  - `movement_pattern_id`: pattern_001557
  - `movement_month`: 2021-07
  - `from_position`: 129141135694
  - `to_position`: 50004135
  - `to_job_profile_id`: R0470.0
  - `movement_count`: 3
  - `unique_employees`: 1
  - `avg_days_between`: 0.0
  - `pct_total_movements`: 0.25
  - `movement_type`: lateral
  - `created_timestamp`: 2025-08-07T10:15:33.484367

---

### 6. **analytics_pathway_predictions** - 0 records

```sql
CREATE TABLE analytics_pathway_predictions (
    prediction_id TEXT PRIMARY KEY,
    from_job_profile_id TEXT,
    to_job_profile_id TEXT,
    ml_predicted_movements REAL,
    pathway_volume_percentile REAL,
    pathway_volume_category TEXT,
    prediction_interval_lower_80pct REAL,
    prediction_interval_upper_80pct REAL,
    prediction_interval_width_80pct REAL,
    model_agreement_fraction TEXT,
    models_agreeing_count INTEGER,
    agreement_rate_decimal REAL,
    prediction_random_forest REAL,
    prediction_xgboost REAL,
    prediction_gradient_boosting REAL,
    historical_sample_size INTEGER,
    ensemble_standard_deviation REAL,
    prediction_coefficient_of_variation_percent REAL,
    from_job_profile_name TEXT,
    to_job_profile_name TEXT,
    training_algorithm TEXT DEFAULT 'ensemble_v1.0',
    training_timestamp TEXT,
    created_timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);
```

**Foreign Key Relationships:**

- `to_job_profile_id` â†’ `core_job_architecture.JobProfileID`
- `from_job_profile_id` â†’ `core_job_architecture.JobProfileID`

**Column Statistics:**

- **prediction_id**: 0 unique values (0 non-null), avg length 0
- **from_job_profile_id**: 0 unique values (0 non-null), avg length 0
- **to_job_profile_id**: 0 unique values (0 non-null), avg length 0
- **ml_predicted_movements**: 0 unique values (0 non-null), range 0.0000 - 0.0000, avg 0.0000
- **pathway_volume_percentile**: 0 unique values (0 non-null), range 0.0000 - 0.0000, avg 0.0000
- **pathway_volume_category**: 0 unique values (0 non-null), avg length 0
- **prediction_interval_lower_80pct**: 0 unique values (0 non-null), range 0.0000 - 0.0000, avg 0.0000
- **prediction_interval_upper_80pct**: 0 unique values (0 non-null), range 0.0000 - 0.0000, avg 0.0000
- **prediction_interval_width_80pct**: 0 unique values (0 non-null), range 0.0000 - 0.0000, avg 0.0000
- **model_agreement_fraction**: 0 unique values (0 non-null), avg length 0
- **models_agreeing_count**: 0 unique values (0 non-null), range 0 - 0
- **agreement_rate_decimal**: 0 unique values (0 non-null), range 0.0000 - 0.0000, avg 0.0000
- **prediction_random_forest**: 0 unique values (0 non-null), range 0.0000 - 0.0000, avg 0.0000
- **prediction_xgboost**: 0 unique values (0 non-null), range 0.0000 - 0.0000, avg 0.0000
- **prediction_gradient_boosting**: 0 unique values (0 non-null), range 0.0000 - 0.0000, avg 0.0000
- **historical_sample_size**: 0 unique values (0 non-null), range 0 - 0
- **ensemble_standard_deviation**: 0 unique values (0 non-null), range 0.0000 - 0.0000, avg 0.0000
- **prediction_coefficient_of_variation_percent**: 0 unique values (0 non-null), range 0.0000 - 0.0000, avg 0.0000
- **from_job_profile_name**: 0 unique values (0 non-null), avg length 0
- **to_job_profile_name**: 0 unique values (0 non-null), avg length 0
- **training_algorithm**: 0 unique values (0 non-null), avg length 0
- **training_timestamp**: 0 unique values (0 non-null), avg length 0
- **created_timestamp**: 0 unique values (0 non-null), avg length 0

**Sample Data by Column:**


### 7. **analytics_skill_bundles** - 2,057 records

```sql
CREATE TABLE analytics_skill_bundles (
    skill_id TEXT PRIMARY KEY,
    skill_name TEXT,
    category TEXT,
    subcategory TEXT,
    skill_type TEXT,
    total_occurrences INTEGER,
    jobs_count INTEGER,
    prevalence_percent REAL,
    cluster_id INTEGER PRIMARY KEY,
    bundle_name TEXT,
    bundle_description TEXT,
    bundle_rationale TEXT,
    bundle_size INTEGER,
    is_specialized BOOLEAN,
    sample_skills TEXT,
    sample_job_functions TEXT,
    bundle_confidence REAL,
    silhouette_score REAL,
    intra_bundle_similarity REAL,
    inter_bundle_distance REAL,
    clustering_algorithm TEXT,
    similarity_method TEXT,
    algorithm_parameters TEXT,
    analysis_date TEXT,
    created_timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);
```

**Foreign Key Relationships:**

- `skill_id` â†’ `core_skills_taxonomy.Skill_ID`

**Column Statistics:**

- **skill_id**: 2,057 unique values (2,057 non-null), avg length 20.0
- **skill_name**: 2,057 unique values (2,057 non-null), avg length 21.71
- **category**: 27 unique values (2,057 non-null), avg length 17.63
- **subcategory**: 240 unique values (2,057 non-null), avg length 21.11
- **skill_type**: 3 unique values (2,057 non-null), avg length 16.56
- **total_occurrences**: 118 unique values (2,057 non-null), range 1 - 666
- **jobs_count**: 118 unique values (2,057 non-null), range 1 - 666
- **prevalence_percent**: 118 unique values (2,057 non-null), range 0.1400 - 93.1500, avg 2.7228
- **cluster_id**: 27 unique values (2,057 non-null), range 0 - 26
- **bundle_name**: 27 unique values (2,057 non-null), avg length 44.29
- **bundle_description**: 27 unique values (2,057 non-null), avg length 67.63
- **bundle_rationale**: 27 unique values (2,057 non-null), avg length 48.63
- **bundle_size**: 24 unique values (2,057 non-null), range 3 - 456
- **sample_skills**: 27 unique values (2,057 non-null), avg length 63.35
- **sample_job_functions**: 1 unique values (2,057 non-null), avg length 16.0
- **bundle_confidence**: 0 unique values (0 non-null), range 0.0000 - 0.0000, avg 0.0000
- **silhouette_score**: 0 unique values (0 non-null), range 0.0000 - 0.0000, avg 0.0000
- **intra_bundle_similarity**: 0 unique values (0 non-null), range 0.0000 - 0.0000, avg 0.0000
- **inter_bundle_distance**: 0 unique values (0 non-null), range 0.0000 - 0.0000, avg 0.0000
- **clustering_algorithm**: 0 unique values (0 non-null), avg length 0
- **similarity_method**: 0 unique values (0 non-null), avg length 0
- **algorithm_parameters**: 0 unique values (0 non-null), avg length 0
- **analysis_date**: 0 unique values (0 non-null), avg length 0
- **created_timestamp**: 46 unique values (2,057 non-null), avg length 26.0

**Data Quality - Completeness:**

- **skill_id**: 100% complete
- **skill_name**: 100% complete
- **category**: 100% complete
- **subcategory**: 100% complete
- **skill_type**: 100% complete
- **total_occurrences**: 100% complete
- **jobs_count**: 100% complete
- **prevalence_percent**: 100% complete
- **cluster_id**: 100% complete
- **bundle_name**: 100% complete
- **bundle_description**: 100% complete
- **bundle_rationale**: 100% complete
- **bundle_size**: 100% complete
- **is_specialized**: 100% complete
- **sample_skills**: 100% complete
- **sample_job_functions**: 100% complete
- **bundle_confidence**: 0.0% complete (2,057 null values)
- **silhouette_score**: 0.0% complete (2,057 null values)
- **intra_bundle_similarity**: 0.0% complete (2,057 null values)
- **inter_bundle_distance**: 0.0% complete (2,057 null values)
- **clustering_algorithm**: 0.0% complete (2,057 null values)
- **similarity_method**: 0.0% complete (2,057 null values)
- **algorithm_parameters**: 0.0% complete (2,057 null values)
- **analysis_date**: 0.0% complete (2,057 null values)
- **created_timestamp**: 100% complete

**Data Quality - Duplicates:**

- ✅ No duplicate records found

**Sample Data by Column:**

- **skill_id**: `BGS10EE289B9FDE2C4B1`, `BGS11665AC6BD06C5EBD`, `BGS117E3FE9519A5B542`, `BGS1241B6719A7FE041D`, `BGS1250D82C4B027A171`, `BGS147DBB4CF132F0523`, `BGS152BE1A314EFF3FE3`, `BGS166A638195D1E2BAE`, `BGS16C952D775A16E650`, `BGS1737E89A3E6B7A57C`
- **skill_name**: `A3 Problem Solving Techniques`, `ADP Enterprise`, `AWS Certified DevOps Engineer`, `AWS Devops`, `AWS Identity And Access Man...`, `Access Controls`, `Account Development`, `Account Growth`, `Account Management`, `Account Reconciliation`
- **category**: `Administration`, `Analysis`, `Architecture and Construction`, `Business`, `Customer and Client Support`, `Design`, `Economics, Policy, and Soci...`, `Education and Training`, `Engineering`, `Environment`
- **subcategory**: `Account Management`, `Accounting and Finance Soft...`, `Accounts Payable and Receiv...`, `Administrative Support and ...`, `Agile Software Development`, `Animation and Game Design`, `Application Programming Int...`, `Architectural Design`, `Artificial Intelligence and...`, `Auditing`
- **skill_type**: `Certification`, `Common Skill`, `Specialized Skill`
- **total_occurrences**: `1`, `2`, `3`, `4`, `5`, `6`, `7`, `8`, `9`, `10`
- **jobs_count**: `1`, `2`, `3`, `4`, `5`, `6`, `7`, `8`, `9`, `10`
- **prevalence_percent**: `0.14`, `0.28`, `0.42`, `0.56`, `0.7`, `0.84`, `0.98`, `1.12`, `1.26`, `1.4`
- **cluster_id**: `0`, `1`, `2`, `3`, `4`, `5`, `6`, `7`, `8`, `9`
- **bundle_name**: `Administration Skills Bundl...`, `Analysis Skills Bundle (91 ...`, `Architecture and Constructi...`, `Business Skills Bundle (434...`, `Customer and Client Support...`, `Design Skills Bundle (42 sk...`, `Economics, Policy, and Soci...`, `Education and Training Skil...`, `Engineering Skills Bundle (...`, `Environment Skills Bundle (...`
- **bundle_description**: `Collection of Administratio...`, `Collection of Analysis skil...`, `Collection of Architecture ...`, `Collection of Business skil...`, `Collection of Customer and ...`, `Collection of Design skills...`, `Collection of Economics, Po...`, `Collection of Education and...`, `Collection of Engineering s...`, `Collection of Environment s...`
- **bundle_rationale**: `Grouped by Administration c...`, `Grouped by Analysis categor...`, `Grouped by Architecture and...`, `Grouped by Business categor...`, `Grouped by Customer and Cli...`, `Grouped by Design category ...`, `Grouped by Economics, Polic...`, `Grouped by Education and Tr...`, `Grouped by Engineering cate...`, `Grouped by Environment cate...`
- **bundle_size**: `3`, `7`, `9`, `11`, `14`, `19`, `20`, `21`, `22`, `23`
- **is_specialized**: `0`
- **sample_skills**: `Catering Management; Cateri...`, `Customer Advocacy; Customer...`, `Customer Centricity; Data A...`, `Customer Retention; Custome...`, `Employee Coaching; Employee...`, `Environmental Risk Assessme...`, `Financial Modeling; Financi...`, `Goal Setting; Customer Insi...`, `IT Security Documentation; ...`, `Influencing Skills; Emotion...`
- **sample_job_functions**: `Analysis pending`
- **created_timestamp**: `2025-08-08T13:51:05.600221`, `2025-08-08T13:51:05.605307`, `2025-08-08T13:51:05.610334`, `2025-08-08T13:51:05.612126`, `2025-08-08T13:51:05.620551`, `2025-08-08T13:51:05.627992`, `2025-08-08T13:51:05.630510`, `2025-08-08T13:51:05.632709`, `2025-08-08T13:51:05.634716`, `2025-08-08T13:51:05.636720`

**Sample Complete Records:**

**Record 1:**
  - `skill_id`: ES439D5D4E1DA572EFB8
  - `skill_name`: Customer Centricity
  - `category`: Analysis
  - `subcategory`: Business Intelligence
  - `skill_type`: Specialized Skill
  - `total_occurrences`: 666
  - `jobs_count`: 666
  - `prevalence_percent`: 93.15
  - `cluster_id`: 0
  - `bundle_name`: Analysis Skills Bundle (91 skills)
  - `bundle_description`: Collection of Analysis skills with 3.1% average...
  - `bundle_rationale`: Grouped by Analysis category similarity
  - `bundle_size`: 91
  - `is_specialized`: 0
  - `sample_skills`: Customer Centricity; Data Analysis; Data Literacy
  - `sample_job_functions`: Analysis pending
  - `created_timestamp`: 2025-08-08T13:51:05.600221

**Record 2:**
  - `skill_id`: KS120GV6C72JMSZKMTD7
  - `skill_name`: Data Analysis
  - `category`: Analysis
  - `subcategory`: Data Analysis
  - `skill_type`: Specialized Skill
  - `total_occurrences`: 205
  - `jobs_count`: 205
  - `prevalence_percent`: 28.67
  - `cluster_id`: 0
  - `bundle_name`: Analysis Skills Bundle (91 skills)
  - `bundle_description`: Collection of Analysis skills with 3.1% average...
  - `bundle_rationale`: Grouped by Analysis category similarity
  - `bundle_size`: 91
  - `is_specialized`: 0
  - `sample_skills`: Customer Centricity; Data Analysis; Data Literacy
  - `sample_job_functions`: Analysis pending
  - `created_timestamp`: 2025-08-08T13:51:05.600221

**Record 3:**
  - `skill_id`: ES476D9219E938F5CB96
  - `skill_name`: Data Literacy
  - `category`: Analysis
  - `subcategory`: Data Science
  - `skill_type`: Specialized Skill
  - `total_occurrences`: 136
  - `jobs_count`: 136
  - `prevalence_percent`: 19.02
  - `cluster_id`: 0
  - `bundle_name`: Analysis Skills Bundle (91 skills)
  - `bundle_description`: Collection of Analysis skills with 3.1% average...
  - `bundle_rationale`: Grouped by Analysis category similarity
  - `bundle_size`: 91
  - `is_specialized`: 0
  - `sample_skills`: Customer Centricity; Data Analysis; Data Literacy
  - `sample_job_functions`: Analysis pending
  - `created_timestamp`: 2025-08-08T13:51:05.600221

---

### 8. **analytics_skill_demand_trends** - 0 records

```sql
CREATE TABLE analytics_skill_demand_trends (
    skill_id TEXT PRIMARY KEY,
    skill_name TEXT,
    category TEXT,
    skill_type TEXT,
    jobs_requiring_skill INTEGER,
    total_skill_instances INTEGER,
    current_prevalence_percent REAL,
    short_term_cagr REAL,
    medium_term_cagr REAL,
    long_term_cagr REAL,
    velocity_category TEXT,
    trend_direction TEXT,
    trend_strength TEXT,
    trend_confidence REAL,
    total_movements INTEGER,
    total_recency_weighted_movements REAL,
    recency_weighted_growth_pct REAL,
    projected_demand_1yr REAL,
    projected_demand_2yr REAL,
    projected_demand_3yr REAL,
    analysis_windows TEXT,
    velocity_thresholds TEXT,
    data_quality_score REAL,
    analysis_date TEXT,
    created_timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);
```

**Foreign Key Relationships:**

- `skill_id` â†’ `core_skills_taxonomy.Skill_ID`

**Column Statistics:**

- **skill_id**: 0 unique values (0 non-null), avg length 0
- **skill_name**: 0 unique values (0 non-null), avg length 0
- **category**: 0 unique values (0 non-null), avg length 0
- **skill_type**: 0 unique values (0 non-null), avg length 0
- **jobs_requiring_skill**: 0 unique values (0 non-null), range 0 - 0
- **total_skill_instances**: 0 unique values (0 non-null), range 0 - 0
- **current_prevalence_percent**: 0 unique values (0 non-null), range 0.0000 - 0.0000, avg 0.0000
- **short_term_cagr**: 0 unique values (0 non-null), range 0.0000 - 0.0000, avg 0.0000
- **medium_term_cagr**: 0 unique values (0 non-null), range 0.0000 - 0.0000, avg 0.0000
- **long_term_cagr**: 0 unique values (0 non-null), range 0.0000 - 0.0000, avg 0.0000
- **velocity_category**: 0 unique values (0 non-null), avg length 0
- **trend_direction**: 0 unique values (0 non-null), avg length 0
- **trend_strength**: 0 unique values (0 non-null), avg length 0
- **trend_confidence**: 0 unique values (0 non-null), range 0.0000 - 0.0000, avg 0.0000
- **total_movements**: 0 unique values (0 non-null), range 0 - 0
- **total_recency_weighted_movements**: 0 unique values (0 non-null), range 0.0000 - 0.0000, avg 0.0000
- **recency_weighted_growth_pct**: 0 unique values (0 non-null), range 0.0000 - 0.0000, avg 0.0000
- **projected_demand_1yr**: 0 unique values (0 non-null), range 0.0000 - 0.0000, avg 0.0000
- **projected_demand_2yr**: 0 unique values (0 non-null), range 0.0000 - 0.0000, avg 0.0000
- **projected_demand_3yr**: 0 unique values (0 non-null), range 0.0000 - 0.0000, avg 0.0000
- **analysis_windows**: 0 unique values (0 non-null), avg length 0
- **velocity_thresholds**: 0 unique values (0 non-null), avg length 0
- **data_quality_score**: 0 unique values (0 non-null), range 0.0000 - 0.0000, avg 0.0000
- **analysis_date**: 0 unique values (0 non-null), avg length 0
- **created_timestamp**: 0 unique values (0 non-null), avg length 0

**Sample Data by Column:**


### 9. **analytics_skill_rarity** - 2,059 records

```sql
CREATE TABLE analytics_skill_rarity (
    skill_id TEXT PRIMARY KEY,
    skill_name TEXT NOT NULL,
    category TEXT,
    subcategory TEXT,
    skill_type TEXT,
    total_profiles_with_skill INTEGER,
    total_jobs INTEGER,
    prevalence_percentage REAL,
    rarity_category TEXT,
    rarity_score REAL,
    is_defining_skill BOOLEAN,
    defining_for_jobs_count INTEGER,
    defining_for_jobs TEXT,
    analysis_date TEXT,
    algorithm_version TEXT,
    created_timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);
```

**Foreign Key Relationships:**

- `skill_id` â†’ `core_skills_taxonomy.Skill_ID`

**Column Statistics:**

- **skill_id**: 2,059 unique values (2,059 non-null), avg length 20.0
- **skill_name**: 2,059 unique values (2,059 non-null), avg length 21.71
- **category**: 29 unique values (2,059 non-null), avg length 17.64
- **subcategory**: 242 unique values (2,059 non-null), avg length 21.11
- **skill_type**: 3 unique values (2,059 non-null), avg length 16.56
- **total_profiles_with_skill**: 118 unique values (2,059 non-null), range 1 - 666
- **total_jobs**: 1 unique values (2,059 non-null), range 715 - 715
- **prevalence_percentage**: 118 unique values (2,059 non-null), range 0.1400 - 93.1500, avg 2.7209
- **rarity_category**: 4 unique values (2,059 non-null), avg length 4.39
- **rarity_score**: 118 unique values (2,059 non-null), range 6.8500 - 99.8600, avg 97.2791
- **defining_for_jobs_count**: 1 unique values (2,059 non-null), range 0 - 0
- **defining_for_jobs**: 1 unique values (2,059 non-null), avg length 0
- **analysis_date**: 1 unique values (2,059 non-null), avg length 10.0
- **algorithm_version**: 1 unique values (2,059 non-null), avg length 20.0
- **created_timestamp**: 1 unique values (2,059 non-null), avg length 19.0

**Data Quality - Completeness:**

- **skill_id**: 100% complete
- **skill_name**: 100% complete
- **category**: 100% complete
- **subcategory**: 100% complete
- **skill_type**: 100% complete
- **total_profiles_with_skill**: 100% complete
- **total_jobs**: 100% complete
- **prevalence_percentage**: 100% complete
- **rarity_category**: 100% complete
- **rarity_score**: 100% complete
- **is_defining_skill**: 100% complete
- **defining_for_jobs_count**: 100% complete
- **defining_for_jobs**: 100% complete
- **analysis_date**: 100% complete
- **algorithm_version**: 100% complete
- **created_timestamp**: 100% complete

**Data Quality - Duplicates:**

- ✅ No duplicate records found

**Sample Data by Column:**

- **skill_id**: `BGS10EE289B9FDE2C4B1`, `BGS11665AC6BD06C5EBD`, `BGS117E3FE9519A5B542`, `BGS1241B6719A7FE041D`, `BGS1250D82C4B027A171`, `BGS147DBB4CF132F0523`, `BGS152BE1A314EFF3FE3`, `BGS166A638195D1E2BAE`, `BGS16C952D775A16E650`, `BGS1737E89A3E6B7A57C`
- **skill_name**: `A3 Problem Solving Techniques`, `ADP Enterprise`, `AWS Certified DevOps Engineer`, `AWS Devops`, `AWS Identity And Access Man...`, `Access Controls`, `Account Development`, `Account Growth`, `Account Management`, `Account Reconciliation`
- **category**: `Administration`, `Analysis`, `Architecture and Construction`, `Business`, `Customer and Client Support`, `Design`, `Economics, Policy, and Soci...`, `Education and Training`, `Energy and Utilities`, `Engineering`
- **subcategory**: `Account Management`, `Accounting and Finance Soft...`, `Accounts Payable and Receiv...`, `Administrative Support and ...`, `Agile Software Development`, `Animation and Game Design`, `Application Programming Int...`, `Architectural Design`, `Artificial Intelligence and...`, `Auditing`
- **skill_type**: `Certification`, `Common Skill`, `Specialized Skill`
- **total_profiles_with_skill**: `1`, `2`, `3`, `4`, `5`, `6`, `7`, `8`, `9`, `10`
- **total_jobs**: `715`
- **prevalence_percentage**: `0.14`, `0.28`, `0.42`, `0.56`, `0.7`, `0.84`, `0.98`, `1.12`, `1.26`, `1.4`
- **rarity_category**: `Common`, `Rare`, `Uncommon`, `Universal`
- **rarity_score**: `6.85`, `6.99`, `8.39`, `9.09`, `9.37`, `9.65`, `9.79`, `9.93`, `10.21`, `47.27`
- **is_defining_skill**: `0`, `1`
- **defining_for_jobs_count**: `0`
- **defining_for_jobs**: ``
- **analysis_date**: `2025-08-07`
- **algorithm_version**: `rarity_analyzer_v1.0`
- **created_timestamp**: `2025-08-07 02:14:35`

**Sample Complete Records:**

**Record 1:**
  - `skill_id`: BGS11665AC6BD06C5EBD
  - `skill_name`: Payroll Reporting
  - `category`: Human Resources
  - `subcategory`: Payroll
  - `skill_type`: Specialized Skill
  - `total_profiles_with_skill`: 1
  - `total_jobs`: 715
  - `prevalence_percentage`: 0.14
  - `rarity_category`: Rare
  - `rarity_score`: 99.86
  - `is_defining_skill`: 1
  - `defining_for_jobs_count`: 0
  - `defining_for_jobs`: 
  - `analysis_date`: 2025-08-07
  - `algorithm_version`: rarity_analyzer_v1.0
  - `created_timestamp`: 2025-08-07 02:14:35

**Record 2:**
  - `skill_id`: BGS166A638195D1E2BAE
  - `skill_name`: Account Strategy
  - `category`: Sales
  - `subcategory`: Account Management
  - `skill_type`: Specialized Skill
  - `total_profiles_with_skill`: 1
  - `total_jobs`: 715
  - `prevalence_percentage`: 0.14
  - `rarity_category`: Rare
  - `rarity_score`: 99.86
  - `is_defining_skill`: 1
  - `defining_for_jobs_count`: 0
  - `defining_for_jobs`: 
  - `analysis_date`: 2025-08-07
  - `algorithm_version`: rarity_analyzer_v1.0
  - `created_timestamp`: 2025-08-07 02:14:35

**Record 3:**
  - `skill_id`: BGS2EBE8AB8957186FB4
  - `skill_name`: Construction Inspection
  - `category`: Architecture and Construction
  - `subcategory`: Construction Inspection
  - `skill_type`: Specialized Skill
  - `total_profiles_with_skill`: 1
  - `total_jobs`: 715
  - `prevalence_percentage`: 0.14
  - `rarity_category`: Rare
  - `rarity_score`: 99.86
  - `is_defining_skill`: 1
  - `defining_for_jobs_count`: 0
  - `defining_for_jobs`: 
  - `analysis_date`: 2025-08-07
  - `algorithm_version`: rarity_analyzer_v1.0
  - `created_timestamp`: 2025-08-07 02:14:35

---

### 10. **analytics_specialized_skills** - 0 records

```sql
CREATE TABLE analytics_specialized_skills (
    skill_id TEXT PRIMARY KEY,
    skill_name TEXT,
    category TEXT,
    subcategory TEXT,
    skill_type TEXT,
    jobs_count INTEGER,
    prevalence_percent REAL,
    specialization_score REAL,
    rarity_rank INTEGER,
    specialization_reason TEXT,
    specialization_category TEXT,
    market_context TEXT,
    strategic_importance TEXT,
    skill_lifecycle_stage TEXT,
    investment_recommendation TEXT,
    related_skills TEXT,
    typical_job_functions TEXT,
    training_availability TEXT,
    external_market_demand TEXT,
    analysis_methodology TEXT,
    confidence_level TEXT,
    last_review_date TEXT,
    next_review_date TEXT,
    created_timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);
```

**Foreign Key Relationships:**

- `skill_id` â†’ `core_skills_taxonomy.Skill_ID`

**Column Statistics:**

- **skill_id**: 0 unique values (0 non-null), avg length 0
- **skill_name**: 0 unique values (0 non-null), avg length 0
- **category**: 0 unique values (0 non-null), avg length 0
- **subcategory**: 0 unique values (0 non-null), avg length 0
- **skill_type**: 0 unique values (0 non-null), avg length 0
- **jobs_count**: 0 unique values (0 non-null), range 0 - 0
- **prevalence_percent**: 0 unique values (0 non-null), range 0.0000 - 0.0000, avg 0.0000
- **specialization_score**: 0 unique values (0 non-null), range 0.0000 - 0.0000, avg 0.0000
- **rarity_rank**: 0 unique values (0 non-null), range 0 - 0
- **specialization_reason**: 0 unique values (0 non-null), avg length 0
- **specialization_category**: 0 unique values (0 non-null), avg length 0
- **market_context**: 0 unique values (0 non-null), avg length 0
- **strategic_importance**: 0 unique values (0 non-null), avg length 0
- **skill_lifecycle_stage**: 0 unique values (0 non-null), avg length 0
- **investment_recommendation**: 0 unique values (0 non-null), avg length 0
- **related_skills**: 0 unique values (0 non-null), avg length 0
- **typical_job_functions**: 0 unique values (0 non-null), avg length 0
- **training_availability**: 0 unique values (0 non-null), avg length 0
- **external_market_demand**: 0 unique values (0 non-null), avg length 0
- **analysis_methodology**: 0 unique values (0 non-null), avg length 0
- **confidence_level**: 0 unique values (0 non-null), avg length 0
- **last_review_date**: 0 unique values (0 non-null), avg length 0
- **next_review_date**: 0 unique values (0 non-null), avg length 0
- **created_timestamp**: 0 unique values (0 non-null), avg length 0

**Sample Data by Column:**


### 11. **core_colleague_positions_history** - 899,675 records

```sql
CREATE TABLE core_colleague_positions_history (
    Week Ending TEXT PRIMARY KEY,
    Employee Number INTEGER,
    Operational BOOLEAN,
    Position Start Date TEXT,
    PosIDLookupKey REAL PRIMARY KEY,
    Position Number INTEGER,
    created_timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);
```

**Column Statistics:**

- **Week Ending**: 212 unique values (899,675 non-null), avg length 10.0
- **Employee Number**: 197,224 unique values (899,675 non-null), range 50000852 - 144999901
- **Position Start Date**: 1,796 unique values (899,675 non-null), avg length 10.0
- **PosIDLookupKey**: 5,000 unique values (899,675 non-null), range 100018582384.4458 - 299995324220.6057, avg 199063195283.3204
- **Position Number**: 5,000 unique values (899,675 non-null), range 50000000 - 50004999
- **created_timestamp**: 77 unique values (899,675 non-null), avg length 19.0

**Data Quality - Completeness:**

- **Week Ending**: 100% complete
- **Employee Number**: 100% complete
- **Operational**: 100% complete
- **Position Start Date**: 100% complete
- **PosIDLookupKey**: 100% complete
- **Position Number**: 100% complete
- **created_timestamp**: 100% complete

**Data Quality - Duplicates:**

- ✅ No duplicate records found

**Sample Data by Column:**

- **Week Ending**: `01/04/2022`, `01/04/2023`, `01/04/2025`, `01/07/2022`, `01/07/2023`, `01/07/2025`, `01/10/2021`, `01/10/2022`, `01/10/2023`, `01/10/2024`
- **Employee Number**: `50000852`, `50000864`, `50000896`, `50000976`, `50001005`, `50001094`, `50001172`, `50001307`, `50001447`, `50001563`
- **Operational**: `0`, `1`
- **Position Start Date**: `01/01/2021`, `01/01/2022`, `01/01/2023`, `01/01/2024`, `01/01/2025`, `01/02/2021`, `01/02/2022`, `01/02/2023`, `01/02/2024`, `01/02/2025`
- **PosIDLookupKey**: `100018582384.44585`, `100108586341.40344`, `100108953649.22575`, `100113396333.1975`, `100114678274.3968`, `100130925176.4322`, `100153832334.07011`, `100290527906.73949`, `100291124499.31078`, `100316183445.16624`
- **Position Number**: `50000000`, `50000001`, `50000002`, `50000003`, `50000004`, `50000005`, `50000006`, `50000007`, `50000008`, `50000009`
- **created_timestamp**: `2025-08-07 00:04:05`, `2025-08-07 00:04:06`, `2025-08-07 00:04:07`, `2025-08-07 00:04:08`, `2025-08-07 00:04:09`, `2025-08-07 00:04:10`, `2025-08-07 00:04:11`, `2025-08-07 00:04:12`, `2025-08-07 00:04:13`, `2025-08-07 00:04:14`

**Sample Complete Records:**

**Record 1:**
  - `Week Ending`: 02/07/2021
  - `Employee Number`: 50042370
  - `Operational`: 0
  - `Position Start Date`: 03/09/2020
  - `PosIDLookupKey`: 250478233022.2972
  - `Position Number`: 50000303
  - `created_timestamp`: 2025-08-07 00:04:05

**Record 2:**
  - `Week Ending`: 02/07/2021
  - `Employee Number`: 56492009
  - `Operational`: 1
  - `Position Start Date`: 12/10/2020
  - `PosIDLookupKey`: 108663496530.68349
  - `Position Number`: 50001291
  - `created_timestamp`: 2025-08-07 00:04:05

**Record 3:**
  - `Week Ending`: 02/07/2021
  - `Employee Number`: 50713050
  - `Operational`: 0
  - `Position Start Date`: 22/12/2020
  - `PosIDLookupKey`: 188129909996.23376
  - `Position Number`: 50003452
  - `created_timestamp`: 2025-08-07 00:04:05

---

### 12. **core_job_architecture** - 715 records

```sql
CREATE TABLE core_job_architecture (
    JobProfileID TEXT PRIMARY KEY,
    JobProfile TEXT NOT NULL,
    JobFunction TEXT,
    JobCategory TEXT,
    ManagementLevel TEXT,
    JobID TEXT,
    Job TEXT,
    ProfileTitleSuffix TEXT,
    JobSubFunctionID TEXT,
    JobSubFunction TEXT,
    JobFunctionID TEXT,
    JobCategoryID TEXT,
    Customer_Facing TEXT,
    is_Banker TEXT,
    Executive_Leadership_Group TEXT,
    Accountability_Scope TEXT,
    created_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);
```

**Column Statistics:**

- **JobProfileID**: 715 unique values (715 non-null), avg length 7.0
- **JobProfile**: 309 unique values (715 non-null), avg length 22.48
- **JobFunction**: 22 unique values (715 non-null), avg length 19.57
- **JobCategory**: 4 unique values (715 non-null), avg length 10.87
- **ManagementLevel**: 8 unique values (715 non-null), avg length 7.02
- **JobID**: 240 unique values (715 non-null), avg length 5.0
- **Job**: 35 unique values (715 non-null), avg length 17.92
- **ProfileTitleSuffix**: 16 unique values (715 non-null), avg length 8.92
- **JobSubFunctionID**: 526 unique values (715 non-null), avg length 6.0
- **JobSubFunction**: 110 unique values (715 non-null), avg length 17.58
- **JobFunctionID**: 22 unique values (715 non-null), avg length 5.0
- **JobCategoryID**: 4 unique values (715 non-null), avg length 3.06
- **Customer_Facing**: 3 unique values (715 non-null), avg length 17.64
- **is_Banker**: 3 unique values (715 non-null), avg length 8.38
- **Executive_Leadership_Group**: 2 unique values (715 non-null), avg length 1.24
- **Accountability_Scope**: 3 unique values (715 non-null), avg length 0.72
- **created_timestamp**: 1 unique values (715 non-null), avg length 19.0
- **updated_timestamp**: 1 unique values (715 non-null), avg length 19.0

**Data Quality - Completeness:**

- **JobProfileID**: 100% complete
- **JobProfile**: 100% complete
- **JobFunction**: 100% complete
- **JobCategory**: 100% complete
- **ManagementLevel**: 100% complete
- **JobID**: 100% complete
- **Job**: 100% complete
- **ProfileTitleSuffix**: 100% complete
- **JobSubFunctionID**: 100% complete
- **JobSubFunction**: 100% complete
- **JobFunctionID**: 100% complete
- **JobCategoryID**: 100% complete
- **Customer_Facing**: 100% complete
- **is_Banker**: 100% complete
- **Executive_Leadership_Group**: 100% complete
- **Accountability_Scope**: 100% complete
- **created_timestamp**: 100% complete
- **updated_timestamp**: 100% complete

**Data Quality - Duplicates:**

- ✅ No duplicate records found

**Sample Data by Column:**

- **JobProfileID**: `R0001.5`, `R0001.6`, `R0002.0`, `R0002.1`, `R0002.2`, `R0002.3`, `R0002.4`, `R0003.0`, `R0003.2`, `R0005.1`
- **JobProfile**: `Budget Manager (Ungraded)`, `Budget Manager - 0`, `Budget Manager - 2`, `Budget Manager - 3`, `Budget Manager - 4`, `Budget Manager - 5`, `Budget Manager - 6`, `Budget Manager - 7`, `Budget Manager - II`, `Business Analyst - 0`
- **JobFunction**: `Audit & Assurance`, `Banking Services`, `Business Development`, `Customer Relations`, `Data & Analytics`, `Executive Leadership`, `Facilities & Administration`, `Finance & Treasury`, `Human Resources`, `Investment Management`
- **JobCategory**: `Enabling`, `Executive & General Management`, `Revenue Generating`, `Support`
- **ManagementLevel**: `Group 1`, `Group 2`, `Group 3`, `Group 4`, `Group 5`, `Group 6`, `Group 7`, `Group NA`
- **JobID**: `R0001`, `R0002`, `R0003`, `R0005`, `R0007`, `R0009`, `R0010`, `R0022`, `R0023`, `R0025`
- **Job**: `Budget Manager`, `Business Analyst`, `Business Banker`, `Chief Officer`, `Cloud Architect`, `Compliance Officer`, `Credit Risk Manager`, `Customer Service Representa...`, `Cybersecurity Analyst`, `Data Scientist`
- **ProfileTitleSuffix**: `Advisor`, `Analyst`, `Associate`, `Consultant`, `Group Executive`, `Head of`, `I`, `II`, `III`, `Lead Consultant`
- **JobSubFunctionID**: `JF0002`, `JF0003`, `JF0004`, `JF0005`, `JF0007`, `JF0009`, `JF0011`, `JF0013`, `JF0020`, `JF0021`
- **JobSubFunction**: `Account Management`, `Actuarial Services`, `Anti-Money Laundering`, `Application Support`, `Artificial Intelligence`, `Asset Management`, `Audit & Assurance`, `Basel Compliance`, `Brand Management`, `Budgeting & Forecasting`
- **JobFunctionID**: `JF001`, `JF002`, `JF003`, `JF004`, `JF005`, `JF006`, `JF007`, `JF008`, `JF009`, `JF010`
- **JobCategoryID**: `JC1`, `JC10`, `JC2`, `JC3`
- **Customer_Facing**: ``, `Customer Facing`, `Non-Customer Facing`
- **is_Banker**: ``, `Banker`, `Non-Banker`
- **Executive_Leadership_Group**: ``, `Executive Leadership Group`
- **Accountability_Scope**: ``, `Direct`, `Supports`
- **created_timestamp**: `2025-08-07 00:03:48`
- **updated_timestamp**: `2025-08-07 00:03:48`

**Sample Complete Records:**

**Record 1:**
  - `JobProfileID`: R0001.5
  - `JobProfile`: Payment Systems Analyst - 5
  - `JobFunction`: Data & Analytics
  - `JobCategory`: Support
  - `ManagementLevel`: Group 2
  - `JobID`: R0001
  - `Job`: Payment Systems Analyst
  - `ProfileTitleSuffix`: Senior Manager
  - `JobSubFunctionID`: JF0655
  - `JobSubFunction`: Data Governance
  - `JobFunctionID`: JF016
  - `JobCategoryID`: JC2
  - `Customer_Facing`: Customer Facing
  - `is_Banker`: Non-Banker
  - `Executive_Leadership_Group`: 
  - `Accountability_Scope`: 
  - `created_timestamp`: 2025-08-07 00:03:48
  - `updated_timestamp`: 2025-08-07 00:03:48

**Record 2:**
  - `JobProfileID`: R0001.6
  - `JobProfile`: Settlement Officer - 6
  - `JobFunction`: Data & Analytics
  - `JobCategory`: Support
  - `ManagementLevel`: Group 1
  - `JobID`: R0001
  - `Job`: Settlement Officer
  - `ProfileTitleSuffix`: Associate
  - `JobSubFunctionID`: JF0559
  - `JobSubFunction`: Machine Learning
  - `JobFunctionID`: JF016
  - `JobCategoryID`: JC2
  - `Customer_Facing`: Customer Facing
  - `is_Banker`: Banker
  - `Executive_Leadership_Group`: Executive Leadership Group
  - `Accountability_Scope`: 
  - `created_timestamp`: 2025-08-07 00:03:48
  - `updated_timestamp`: 2025-08-07 00:03:48

**Record 3:**
  - `JobProfileID`: R0002.0
  - `JobProfile`: Sales Manager - II
  - `JobFunction`: Banking Services
  - `JobCategory`: Enabling
  - `ManagementLevel`: Group 4
  - `JobID`: R0002
  - `Job`: Sales Manager
  - `ProfileTitleSuffix`: II
  - `JobSubFunctionID`: JF0204
  - `JobSubFunction`: Investment Banking
  - `JobFunctionID`: JF012
  - `JobCategoryID`: JC1
  - `Customer_Facing`: Customer Facing
  - `is_Banker`: Banker
  - `Executive_Leadership_Group`: 
  - `Accountability_Scope`: 
  - `created_timestamp`: 2025-08-07 00:03:48
  - `updated_timestamp`: 2025-08-07 00:03:48

---

### 13. **core_job_skill_requirements** - 40,170 records

```sql
CREATE TABLE core_job_skill_requirements (
    JobProfileID TEXT PRIMARY KEY,
    Skill_ID TEXT PRIMARY KEY,
    created_timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);
```

**Foreign Key Relationships:**

- `Skill_ID` â†’ `core_skills_taxonomy.Skill_ID`
- `JobProfileID` â†’ `core_job_architecture.JobProfileID`

**Column Statistics:**

- **JobProfileID**: 715 unique values (40,170 non-null), avg length 7.0
- **Skill_ID**: 2,091 unique values (40,170 non-null), avg length 20.0
- **created_timestamp**: 1 unique values (40,170 non-null), avg length 19.0

**Data Quality - Completeness:**

- **JobProfileID**: 100% complete
- **Skill_ID**: 100% complete
- **created_timestamp**: 100% complete

**Data Quality - Duplicates:**

- ✅ No duplicate records found

**Sample Data by Column:**

- **JobProfileID**: `R0001.5`, `R0001.6`, `R0002.0`, `R0002.1`, `R0002.2`, `R0002.3`, `R0002.4`, `R0003.0`, `R0003.2`, `R0005.1`
- **Skill_ID**: `BGS10EE289B9FDE2C4B1`, `BGS11665AC6BD06C5EBD`, `BGS117E3FE9519A5B542`, `BGS1241B6719A7FE041D`, `BGS1250D82C4B027A171`, `BGS147DBB4CF132F0523`, `BGS152BE1A314EFF3FE3`, `BGS166A638195D1E2BAE`, `BGS16C952D775A16E650`, `BGS1737E89A3E6B7A57C`
- **created_timestamp**: `2025-08-07 00:03:49`

**Sample Complete Records:**

**Record 1:**
  - `JobProfileID`: R0001.5
  - `Skill_ID`: BGSD16A8EEF4F5775E15
  - `created_timestamp`: 2025-08-07 00:03:49

**Record 2:**
  - `JobProfileID`: R0001.5
  - `Skill_ID`: ES147CB8BEA5CF1AF1F6
  - `created_timestamp`: 2025-08-07 00:03:49

**Record 3:**
  - `JobProfileID`: R0001.5
  - `Skill_ID`: ES203B9B0426DA590EDF
  - `created_timestamp`: 2025-08-07 00:03:49

---

### 14. **core_position_timeline** - 479,968 records

```sql
CREATE TABLE core_position_timeline (
    position_timeline_id TEXT PRIMARY KEY,
    Week_Ending TEXT,
    Position_Number INTEGER,
    JobProfileID TEXT,
    PosIDLookupKey REAL,
    Organisational_Unit TEXT,
    Cost_Centre_Number INTEGER,
    Position_Title TEXT,
    People_Leader REAL,
    Operational BOOLEAN,
    OrgUnitIDLookupKey INTEGER,
    created_timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);
```

**Foreign Key Relationships:**

- `JobProfileID` â†’ `core_job_architecture.JobProfileID`

**Column Statistics:**

- **position_timeline_id**: 479,968 unique values (479,968 non-null), avg length 18.0
- **Week_Ending**: 212 unique values (479,968 non-null), avg length 10.0
- **Position_Number**: 4,567 unique values (479,968 non-null), range 50000000 - 50004999
- **JobProfileID**: 620 unique values (479,968 non-null), avg length 7.0
- **PosIDLookupKey**: 4,567 unique values (479,968 non-null), range 100018582384.4458 - 299995324220.6057, avg 200142754813.9655
- **Organisational_Unit**: 11 unique values (479,968 non-null), avg length 13.48
- **Cost_Centre_Number**: 90 unique values (479,968 non-null), range 1000 - 9900
- **Position_Title**: 1 unique values (479,968 non-null), avg length 0
- **People_Leader**: 119,555 unique values (479,968 non-null), range 20000014.0297 - 0.0000, avg 6222319.8234
- **OrgUnitIDLookupKey**: 4,567 unique values (479,968 non-null), range 1001435 - 9997791
- **created_timestamp**: 16 unique values (479,968 non-null), avg length 19.0

**Data Quality - Completeness:**

- **position_timeline_id**: 100% complete
- **Week_Ending**: 100% complete
- **Position_Number**: 100% complete
- **JobProfileID**: 100% complete
- **PosIDLookupKey**: 100% complete
- **Organisational_Unit**: 100% complete
- **Cost_Centre_Number**: 100% complete
- **Position_Title**: 100% complete
- **People_Leader**: 100% complete
- **Operational**: 100% complete
- **OrgUnitIDLookupKey**: 100% complete
- **created_timestamp**: 100% complete

**Data Quality - Duplicates:**

- ✅ No duplicate records found

**Sample Data by Column:**

- **position_timeline_id**: `5000000001/04/2022`, `5000000001/04/2023`, `5000000001/07/2022`, `5000000001/07/2023`, `5000000001/10/2021`, `5000000001/10/2022`, `5000000001/10/2023`, `5000000002/06/2024`, `5000000002/07/2021`, `5000000002/07/2022`
- **Week_Ending**: `01/04/2022`, `01/04/2023`, `01/04/2025`, `01/07/2022`, `01/07/2023`, `01/07/2025`, `01/10/2021`, `01/10/2022`, `01/10/2023`, `01/10/2024`
- **Position_Number**: `50000000`, `50000001`, `50000002`, `50000004`, `50000005`, `50000006`, `50000007`, `50000008`, `50000009`, `50000010`
- **JobProfileID**: `R0001.5`, `R0001.6`, `R0002.0`, `R0002.1`, `R0002.2`, `R0003.0`, `R0003.2`, `R0005.1`, `R0009.0`, `R0009.1`
- **PosIDLookupKey**: `100018582384.44585`, `100108586341.40344`, `100108953649.22575`, `100113396333.1975`, `100114678274.3968`, `100130925176.4322`, `100153832334.07011`, `100290527906.73949`, `100291124499.31078`, `100316183445.16624`
- **Organisational_Unit**: `Business Banking`, `Customer Banking`, `Digital & Data`, `Finance`, `Human Resources`, `Investment Banking`, `Legal & Compliance`, `Marketing`, `Operations`, `Risk Management`
- **Cost_Centre_Number**: `1000`, `1100`, `1200`, `1300`, `1400`, `1500`, `1600`, `1700`, `1800`, `1900`
- **Position_Title**: ``
- **People_Leader**: `20000014.02970184`, `20000028.707990576`, `20000033.55052813`, `20000159.471018627`, `20000476.94575564`, `20000618.778659016`, `20000670.06647055`, `20000696.737737726`, `20000824.57050431`, `20000835.13877497`
- **Operational**: `0`, `1`
- **OrgUnitIDLookupKey**: `1001435`, `1001549`, `1008306`, `1010766`, `1010905`, `1012106`, `1014148`, `1016411`, `1018410`, `1023487`
- **created_timestamp**: `2025-08-07 00:03:50`, `2025-08-07 00:03:51`, `2025-08-07 00:03:52`, `2025-08-07 00:03:53`, `2025-08-07 00:03:54`, `2025-08-07 00:03:55`, `2025-08-07 00:03:56`, `2025-08-07 00:03:57`, `2025-08-07 00:03:58`, `2025-08-07 00:03:59`

**Sample Complete Records:**

**Record 1:**
  - `position_timeline_id`: 5000145602/07/2021
  - `Week_Ending`: 02/07/2021
  - `Position_Number`: 50001456
  - `JobProfileID`: R0045.3
  - `PosIDLookupKey`: 273434355949.7322
  - `Organisational_Unit`: Business Banking
  - `Cost_Centre_Number`: 5600
  - `Position_Title`: 
  - `People_Leader`: 
  - `Operational`: 1
  - `OrgUnitIDLookupKey`: 7658793
  - `created_timestamp`: 2025-08-07 00:03:50

**Record 2:**
  - `position_timeline_id`: 5000164002/07/2021
  - `Week_Ending`: 02/07/2021
  - `Position_Number`: 50001640
  - `JobProfileID`: R0075.4
  - `PosIDLookupKey`: 210815052633.6948
  - `Organisational_Unit`: Legal & Compliance
  - `Cost_Centre_Number`: 9600
  - `Position_Title`: 
  - `People_Leader`: 
  - `Operational`: 1
  - `OrgUnitIDLookupKey`: 5132498
  - `created_timestamp`: 2025-08-07 00:03:50

**Record 3:**
  - `position_timeline_id`: 5000071702/07/2021
  - `Week_Ending`: 02/07/2021
  - `Position_Number`: 50000717
  - `JobProfileID`: R0284.5
  - `PosIDLookupKey`: 249149963967.82724
  - `Organisational_Unit`: Operations
  - `Cost_Centre_Number`: 5700
  - `Position_Title`: 
  - `People_Leader`: 22520367.799270414
  - `Operational`: 1
  - `OrgUnitIDLookupKey`: 6668452
  - `created_timestamp`: 2025-08-07 00:03:50

---

### 15. **core_skills_taxonomy** - 38,525 records

```sql
CREATE TABLE core_skills_taxonomy (
    Skill_ID TEXT PRIMARY KEY,
    Skill_Name TEXT NOT NULL,
    Category TEXT,
    Subcategory TEXT,
    SkillType TEXT,
    category_id REAL,
    description TEXT,
    descriptionSource TEXT,
    infoUrl TEXT,
    isLanguage BOOLEAN,
    isSoftware BOOLEAN,
    source_version REAL,
    subcategory_id REAL,
    tag_wikipediaExtract TEXT,
    tag_wikipediaUrl TEXT,
    tags TEXT,
    type TEXT,
    type_id TEXT,
    created_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);
```

**Column Statistics:**

- **Skill_ID**: 38,525 unique values (38,525 non-null), avg length 20.0
- **Skill_Name**: 38,525 unique values (38,525 non-null), avg length 19.7
- **Category**: 34 unique values (38,525 non-null), avg length 17.97
- **Subcategory**: 460 unique values (38,525 non-null), avg length 20.3
- **SkillType**: 3 unique values (38,525 non-null), avg length 16.57
- **category_id**: 34 unique values (38,525 non-null), range 0.0000 - 0.0000, avg 14.6610
- **description**: 37,195 unique values (38,525 non-null), avg length 485.13
- **descriptionSource**: 2,477 unique values (38,525 non-null), avg length 10.9
- **infoUrl**: 38,525 unique values (38,525 non-null), avg length 60.0
- **source_version**: 53 unique values (38,525 non-null), range 8.0000 - 9.9000, avg 9.2224
- **subcategory_id**: 453 unique values (38,525 non-null), range 100.0000 - 0.0000, avg 362.7682
- **tag_wikipediaExtract**: 24,327 unique values (38,525 non-null), avg length 313.01
- **tag_wikipediaUrl**: 24,973 unique values (38,525 non-null), avg length 33.93
- **tags**: 25,633 unique values (38,525 non-null), avg length 406.11
- **type**: 3 unique values (38,525 non-null), avg length 41.57
- **type_id**: 3 unique values (38,525 non-null), avg length 3.0
- **created_timestamp**: 1 unique values (38,525 non-null), avg length 19.0
- **updated_timestamp**: 1 unique values (38,525 non-null), avg length 19.0

**Data Quality - Completeness:**

- **Skill_ID**: 100% complete
- **Skill_Name**: 100% complete
- **Category**: 100% complete
- **Subcategory**: 100% complete
- **SkillType**: 100% complete
- **category_id**: 100% complete
- **description**: 100% complete
- **descriptionSource**: 100% complete
- **infoUrl**: 100% complete
- **isLanguage**: 100% complete
- **isSoftware**: 100% complete
- **source_version**: 100% complete
- **subcategory_id**: 100% complete
- **tag_wikipediaExtract**: 100% complete
- **tag_wikipediaUrl**: 100% complete
- **tags**: 100% complete
- **type**: 100% complete
- **type_id**: 100% complete
- **created_timestamp**: 100% complete
- **updated_timestamp**: 100% complete

**Data Quality - Duplicates:**

- ✅ No duplicate records found

**Sample Data by Column:**

- **Skill_ID**: `BGS1024316C916ACCFA3`, `BGS105C99F084505B956`, `BGS1080D1F8CED414379`, `BGS10AB6DEBB81A2E88C`, `BGS10B5E145CA48862FC`, `BGS10CBE4935DDCAE5AD`, `BGS10EE289B9FDE2C4B1`, `BGS10F3F05054C5731C2`, `BGS10F94E4049444B523`, `BGS110587665F051DF29`
- **Skill_Name**: `.NET Assemblies`, `.NET Code Analysis (FxCop A...`, `.NET Development`, `.NET Framework`, `.NET Framework 1`, `.NET Framework 3`, `.NET Framework 4`, `.NET MAUI (Multi-Platform A...`, `.NET Reflector`, `.NET Remoting`
- **Category**: ``, `Administration`, `Agriculture, Horticulture, ...`, `Analysis`, `Architecture and Construction`, `Business`, `Customer and Client Support`, `Design`, `Economics, Policy, and Soci...`, `Education and Training`
- **Subcategory**: ``, `Account Management`, `Accounting and Finance Soft...`, `Accounts Payable and Receiv...`, `Administrative Support and ...`, `Advanced Customer Service`, `Advanced Patient Care`, `Advertising`, `Aerospace Engineering`, `Agile Software Development`
- **SkillType**: `Certification`, `Common Skill`, `Specialized Skill`
- **category_id**: `0.0`, `1.0`, `2.0`, `3.0`, `4.0`, `5.0`, `6.0`, `7.0`, `8.0`, `9.0`
- **description**: ``, `'Autoroll' refers to TV-sig...`, `'National Lifeguard’ is a l...`, `.NET Assemblies refer to th...`, `.NET Code Analysis (FxCop A...`, `.NET Development refers to ...`, `.NET Framework 1 is a softw...`, `.NET Framework 3 is a softw...`, `.NET Framework 4 is a softw...`, `.NET Framework is a softwar...`
- **descriptionSource**: ``, `LIGHTCAST`, `https://en.wikipedia.org/wi...`, `https://en.wikipedia.org/wi...`, `https://en.wikipedia.org/wi...`, `https://en.wikipedia.org/wi...`, `https://en.wikipedia.org/wi...`, `https://en.wikipedia.org/wi...`, `https://en.wikipedia.org/wi...`, `https://en.wikipedia.org/wi...`
- **infoUrl**: `https://lightcast.io/open-s...`, `https://lightcast.io/open-s...`, `https://lightcast.io/open-s...`, `https://lightcast.io/open-s...`, `https://lightcast.io/open-s...`, `https://lightcast.io/open-s...`, `https://lightcast.io/open-s...`, `https://lightcast.io/open-s...`, `https://lightcast.io/open-s...`, `https://lightcast.io/open-s...`
- **isLanguage**: `0`, `1`
- **isSoftware**: `0`, `1`
- **source_version**: `8.0`, `8.1`, `8.11`, `8.12`, `8.13`, `8.14`, `8.15`, `8.16`, `8.17`, `8.18`
- **subcategory_id**: `100.0`, `101.0`, `102.0`, `105.0`, `106.0`, `107.0`, `108.0`, `109.0`, `110.0`, `111.0`
- **tag_wikipediaExtract**: ``, `"Autofac" is a 1955 science...`, `"Certified Management Consu...`, `"Environmental Quality" is ...`, `"Information display system...`, `"Liners" is a horticultural...`, `"Radar Detector" is the sec...`, `"Stochastic" means being or...`, `"Tubal Reversal," also call...`, `"Unified Science" can refer...`
- **tag_wikipediaUrl**: ``, `https://de.wikipedia.org/wi...`, `https://en.m.wikipedia.org/...`, `https://en.wikipedia.org/wi...`, `https://en.wikipedia.org/wi...`, `https://en.wikipedia.org/wi...`, `https://en.wikipedia.org/wi...`, `https://en.wikipedia.org/wi...`, `https://en.wikipedia.org/wi...`, `https://en.wikipedia.org/wi...`
- **tags**: `[]`, `[{"key": "wikipediaExtract"...`, `[{"key": "wikipediaExtract"...`, `[{"key": "wikipediaExtract"...`, `[{"key": "wikipediaExtract"...`, `[{"key": "wikipediaExtract"...`, `[{"key": "wikipediaExtract"...`, `[{"key": "wikipediaExtract"...`, `[{"key": "wikipediaExtract"...`, `[{"key": "wikipediaExtract"...`
- **type**: `{"id": "ST1", "name": "Spec...`, `{"id": "ST2", "name": "Comm...`, `{"id": "ST3", "name": "Cert...`
- **type_id**: `ST1`, `ST2`, `ST3`
- **created_timestamp**: `2025-08-07 00:03:49`
- **updated_timestamp**: `2025-08-07 00:03:49`

**Sample Complete Records:**

**Record 1:**
  - `Skill_ID`: BGS1024316C916ACCFA3
  - `Skill_Name`: DX Spectrum
  - `Category`: Information Technology
  - `Subcategory`: Enterprise Information Management
  - `SkillType`: Specialized Skill
  - `category_id`: 17.0
  - `description`: 
  - `descriptionSource`: 
  - `infoUrl`: https://lightcast.io/open-skills/skills/BGS1024...
  - `isLanguage`: 0
  - `isSoftware`: 1
  - `source_version`: 8.5
  - `subcategory_id`: 411.0
  - `tag_wikipediaExtract`: 
  - `tag_wikipediaUrl`: 
  - `tags`: []
  - `type`: {"id": "ST1", "name": "Specialized Skill"}
  - `type_id`: ST1
  - `created_timestamp`: 2025-08-07 00:03:49
  - `updated_timestamp`: 2025-08-07 00:03:49

**Record 2:**
  - `Skill_ID`: BGS105C99F084505B956
  - `Skill_Name`: Microsoft Sysprep
  - `Category`: Information Technology
  - `Subcategory`: Software Development Tools
  - `SkillType`: Specialized Skill
  - `category_id`: 17.0
  - `description`: Microsoft Sysprep is a utility tool used to pre...
  - `descriptionSource`: LIGHTCAST
  - `infoUrl`: https://lightcast.io/open-skills/skills/BGS105C...
  - `isLanguage`: 0
  - `isSoftware`: 1
  - `source_version`: 9.33
  - `subcategory_id`: 476.0
  - `tag_wikipediaExtract`: Sysprep is Microsoft's System Preparation Tool ...
  - `tag_wikipediaUrl`: https://en.wikipedia.org/wiki/Sysprep
  - `tags`: [{"key": "wikipediaExtract", "value": "Sysprep ...
  - `type`: {"id": "ST1", "name": "Specialized Skill"}
  - `type_id`: ST1
  - `created_timestamp`: 2025-08-07 00:03:49
  - `updated_timestamp`: 2025-08-07 00:03:49

**Record 3:**
  - `Skill_ID`: BGS1080D1F8CED414379
  - `Skill_Name`: Application Remediation
  - `Category`: Information Technology
  - `Subcategory`: Software Quality Assurance
  - `SkillType`: Specialized Skill
  - `category_id`: 17.0
  - `description`: Application Remediation refers to the process o...
  - `descriptionSource`: LIGHTCAST
  - `infoUrl`: https://lightcast.io/open-skills/skills/BGS1080...
  - `isLanguage`: 0
  - `isSoftware`: 0
  - `source_version`: 9.33
  - `subcategory_id`: 477.0
  - `tag_wikipediaExtract`: 
  - `tag_wikipediaUrl`: 
  - `tags`: []
  - `type`: {"id": "ST1", "name": "Specialized Skill"}
  - `type_id`: ST1
  - `created_timestamp`: 2025-08-07 00:03:49
  - `updated_timestamp`: 2025-08-07 00:03:49

---

### 16. **core_workforce_current** - 35,000 records

```sql
CREATE TABLE core_workforce_current (
    employee_number TEXT PRIMARY KEY,
    position_number TEXT NOT NULL,
    position_name TEXT,
    JobProfileID TEXT,
    Employee_Group TEXT,
    Employee_Subgroup TEXT,
    Salary_Group TEXT,
    Location TEXT,
    Rg TEXT,
    Cty TEXT,
    ORG_UNIT_NAME_1 TEXT,
    ORG_UNIT_NAME_2 TEXT,
    ORG_UNIT_NAME_3 TEXT,
    ORG_UNIT_NAME_4 TEXT,
    ORG_UNIT_NAME_5 TEXT,
    ORG_UNIT_NAME_6 TEXT,
    ORG_UNIT_NAME_7 TEXT,
    ORG_UNIT_NAME_8 TEXT,
    ORG_UNIT_NAME_9 TEXT,
    ORG_UNIT_NAME_10 TEXT,
    created_timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);
```

**Foreign Key Relationships:**

- `JobProfileID` â†’ `core_job_architecture.JobProfileID`

**Column Statistics:**

- **employee_number**: 35,000 unique values (35,000 non-null), avg length 6.0
- **position_number**: 4,997 unique values (35,000 non-null), avg length 8.0
- **position_name**: 580 unique values (35,000 non-null), avg length 21.98
- **JobProfileID**: 628 unique values (35,000 non-null), avg length 7.0
- **Employee_Group**: 4 unique values (35,000 non-null), avg length 8.77
- **Employee_Subgroup**: 3 unique values (35,000 non-null), avg length 8.01
- **Salary_Group**: 9 unique values (35,000 non-null), avg length 7.0
- **Location**: 6 unique values (35,000 non-null), avg length 8.6
- **Rg**: 5 unique values (35,000 non-null), avg length 2.67
- **Cty**: 1 unique values (35,000 non-null), avg length 2.0
- **ORG_UNIT_NAME_1**: 1 unique values (35,000 non-null), avg length 31.0
- **ORG_UNIT_NAME_2**: 6 unique values (35,000 non-null), avg length 20.1
- **ORG_UNIT_NAME_3**: 10 unique values (35,000 non-null), avg length 14.34
- **ORG_UNIT_NAME_4**: 10 unique values (35,000 non-null), avg length 24.53
- **ORG_UNIT_NAME_5**: 30 unique values (35,000 non-null), avg length 7.0
- **ORG_UNIT_NAME_6**: 26 unique values (35,000 non-null), avg length 7.0
- **ORG_UNIT_NAME_7**: 20 unique values (35,000 non-null), avg length 5.55
- **ORG_UNIT_NAME_8**: 50 unique values (35,000 non-null), avg length 8.0
- **ORG_UNIT_NAME_9**: 30 unique values (35,000 non-null), avg length 7.0
- **ORG_UNIT_NAME_10**: 100 unique values (35,000 non-null), avg length 8.0
- **created_timestamp**: 1 unique values (35,000 non-null), avg length 19.0

**Data Quality - Completeness:**

- **employee_number**: 100% complete
- **position_number**: 100% complete
- **position_name**: 100% complete
- **JobProfileID**: 100% complete
- **Employee_Group**: 100% complete
- **Employee_Subgroup**: 100% complete
- **Salary_Group**: 100% complete
- **Location**: 100% complete
- **Rg**: 100% complete
- **Cty**: 100% complete
- **ORG_UNIT_NAME_1**: 100% complete
- **ORG_UNIT_NAME_2**: 100% complete
- **ORG_UNIT_NAME_3**: 100% complete
- **ORG_UNIT_NAME_4**: 100% complete
- **ORG_UNIT_NAME_5**: 100% complete
- **ORG_UNIT_NAME_6**: 100% complete
- **ORG_UNIT_NAME_7**: 100% complete
- **ORG_UNIT_NAME_8**: 100% complete
- **ORG_UNIT_NAME_9**: 100% complete
- **ORG_UNIT_NAME_10**: 100% complete
- **created_timestamp**: 100% complete

**Data Quality - Duplicates:**

- ✅ No duplicate records found

**Sample Data by Column:**

- **employee_number**: `100000`, `100001`, `100002`, `100003`, `100004`, `100005`, `100006`, `100007`, `100008`, `100009`
- **position_number**: `50000000`, `50000001`, `50000002`, `50000003`, `50000004`, `50000005`, `50000006`, `50000007`, `50000008`, `50000009`
- **position_name**: `Analytics Advisor`, `Analytics Analyst`, `Analytics Associate`, `Analytics Consultant`, `Analytics Developer`, `Analytics Director`, `Analytics Engineer`, `Analytics Executive Advisor`, `Analytics Executive Director`, `Analytics Executive Manager`
- **JobProfileID**: `R0001.5`, `R0001.6`, `R0002.0`, `R0002.1`, `R0002.2`, `R0003.0`, `R0003.2`, `R0005.1`, `R0009.0`, `R0009.1`
- **Employee_Group**: `Casual`, `Contractor`, `Fixed Term`, `Permanent`
- **Employee_Subgroup**: `Casual`, `Full Time`, `Part Time`
- **Salary_Group**: `Casual`, `External`, `Group 1`, `Group 2`, `Group 3`, `Group 4`, `Group 5`, `Group 6`, `Group 7`
- **Location**: `Adelaide`, `Brisbane City`, `Docklands`, `Parramatta`, `Perth`, `Sydney`
- **Rg**: `NSW`, `QLD`, `SA`, `VIC`, `WA`
- **Cty**: `AU`
- **ORG_UNIT_NAME_1**: `National Australia Bank Lim...`
- **ORG_UNIT_NAME_2**: `Business & Private Banking`, `Corporate & Institutional B...`, `Customer Banking & Wealth`, `Group Functions`, `NAB Ventures`, `Technology`
- **ORG_UNIT_NAME_3**: `Business Banking`, `Corporate Banking`, `Finance`, `Human Resources`, `Legal & Compliance`, `NAB Ventures`, `Personal Banking`, `Risk Management`, `Technology`, `Wealth Management`
- **ORG_UNIT_NAME_4**: `Business Banking Operations`, `Corporate Banking Operations`, `Finance Strategy`, `Human Resources Strategy`, `Legal & Compliance Strategy`, `NAB Ventures Operations`, `Personal Banking Operations`, `Risk Management Strategy`, `Technology Operations`, `Wealth Management Operations`
- **ORG_UNIT_NAME_5**: `Team 01`, `Team 02`, `Team 03`, `Team 04`, `Team 05`, `Team 06`, `Team 07`, `Team 08`, `Team 09`, `Team 10`
- **ORG_UNIT_NAME_6**: `Squad A`, `Squad B`, `Squad C`, `Squad D`, `Squad E`, `Squad F`, `Squad G`, `Squad H`, `Squad I`, `Squad J`
- **ORG_UNIT_NAME_7**: `Pod 1`, `Pod 10`, `Pod 11`, `Pod 12`, `Pod 13`, `Pod 14`, `Pod 15`, `Pod 16`, `Pod 17`, `Pod 18`
- **ORG_UNIT_NAME_8**: `Unit 001`, `Unit 002`, `Unit 003`, `Unit 004`, `Unit 005`, `Unit 006`, `Unit 007`, `Unit 008`, `Unit 009`, `Unit 010`
- **ORG_UNIT_NAME_9**: `Cell 01`, `Cell 02`, `Cell 03`, `Cell 04`, `Cell 05`, `Cell 06`, `Cell 07`, `Cell 08`, `Cell 09`, `Cell 10`
- **ORG_UNIT_NAME_10**: `Node 001`, `Node 002`, `Node 003`, `Node 004`, `Node 005`, `Node 006`, `Node 007`, `Node 008`, `Node 009`, `Node 010`
- **created_timestamp**: `2025-08-07 00:03:50`

**Sample Complete Records:**

**Record 1:**
  - `employee_number`: 100000
  - `position_number`: 50003311
  - `position_name`: Investment Principal Specialist
  - `JobProfileID`: R0242.3
  - `Employee_Group`: Fixed Term
  - `Employee_Subgroup`: Full Time
  - `Salary_Group`: Group 7
  - `Location`: Brisbane City
  - `Rg`: QLD
  - `Cty`: AU
  - `ORG_UNIT_NAME_1`: National Australia Bank Limited
  - `ORG_UNIT_NAME_2`: Corporate & Institutional Banking
  - `ORG_UNIT_NAME_3`: Technology
  - `ORG_UNIT_NAME_4`: Business Banking Operations
  - `ORG_UNIT_NAME_5`: Team 15
  - `ORG_UNIT_NAME_6`: Squad H
  - `ORG_UNIT_NAME_7`: Pod 15
  - `ORG_UNIT_NAME_8`: Unit 038
  - `ORG_UNIT_NAME_9`: Cell 11
  - `ORG_UNIT_NAME_10`: Node 024
  - `created_timestamp`: 2025-08-07 00:03:50

**Record 2:**
  - `employee_number`: 100001
  - `position_number`: 50003667
  - `position_name`: Operations Vice President
  - `JobProfileID`: R0306.0
  - `Employee_Group`: Permanent
  - `Employee_Subgroup`: Full Time
  - `Salary_Group`: Group 7
  - `Location`: Adelaide
  - `Rg`: SA
  - `Cty`: AU
  - `ORG_UNIT_NAME_1`: National Australia Bank Limited
  - `ORG_UNIT_NAME_2`: Corporate & Institutional Banking
  - `ORG_UNIT_NAME_3`: Human Resources
  - `ORG_UNIT_NAME_4`: Human Resources Strategy
  - `ORG_UNIT_NAME_5`: Team 05
  - `ORG_UNIT_NAME_6`: Squad D
  - `ORG_UNIT_NAME_7`: Pod 19
  - `ORG_UNIT_NAME_8`: Unit 003
  - `ORG_UNIT_NAME_9`: Cell 30
  - `ORG_UNIT_NAME_10`: Node 037
  - `created_timestamp`: 2025-08-07 00:03:50

**Record 3:**
  - `employee_number`: 100002
  - `position_number`: 50000226
  - `position_name`: Audit General Manager
  - `JobProfileID`: R0304.2
  - `Employee_Group`: Fixed Term
  - `Employee_Subgroup`: Casual
  - `Salary_Group`: Group 2
  - `Location`: Sydney
  - `Rg`: NSW
  - `Cty`: AU
  - `ORG_UNIT_NAME_1`: National Australia Bank Limited
  - `ORG_UNIT_NAME_2`: Technology
  - `ORG_UNIT_NAME_3`: Human Resources
  - `ORG_UNIT_NAME_4`: Finance Strategy
  - `ORG_UNIT_NAME_5`: Team 27
  - `ORG_UNIT_NAME_6`: Squad H
  - `ORG_UNIT_NAME_7`: Pod 9
  - `ORG_UNIT_NAME_8`: Unit 030
  - `ORG_UNIT_NAME_9`: Cell 22
  - `ORG_UNIT_NAME_10`: Node 092
  - `created_timestamp`: 2025-08-07 00:03:50

---

### 17. **sys_schema_metadata** - 22 records

```sql
CREATE TABLE sys_schema_metadata (
    metadata_key TEXT PRIMARY KEY,
    metadata_value TEXT,
    metadata_category TEXT,
    description TEXT,
    created_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);
```

**Column Statistics:**

- **metadata_key**: 22 unique values (22 non-null), avg length 27.45
- **metadata_value**: 20 unique values (22 non-null), avg length 9.55
- **metadata_category**: 5 unique values (22 non-null), avg length 8.5
- **description**: 22 unique values (22 non-null), avg length 37.41
- **created_timestamp**: 4 unique values (22 non-null), avg length 19.0
- **updated_timestamp**: 10 unique values (22 non-null), avg length 22.18

**Data Quality - Completeness:**

- **metadata_key**: 100% complete
- **metadata_value**: 100% complete
- **metadata_category**: 100% complete
- **description**: 100% complete
- **created_timestamp**: 100% complete
- **updated_timestamp**: 100% complete

**Data Quality - Duplicates:**

- ✅ No duplicate records found

**Sample Data by Column:**

- **metadata_key**: `analytics_phase_1_completed`, `analytics_phase_1_record_count`, `analytics_tables_count`, `core_tables_count`, `created_date`, `last_data_refresh`, `naming_convention`, `phase0_populated_tables`, `phase_status`, `purpose`
- **metadata_value**: ``, `0`, `1`, `10`, `16`, `19460`, `2.0`, `2025-08-07T10:03:48.371187`, `2057`, `2059`
- **metadata_category**: `analytics_status`, `schema`, `stats`, `table_stats`, `version`
- **description**: `Business-meaningful table n...`, `Completion status for phase_1`, `Current implementation phas...`, `Database purpose`, `Enhanced database schema ve...`, `Number of analytics tables`, `Number of core data tables`, `Number of system tables`, `Number of tables populated ...`, `Record count for analytics_...`
- **created_timestamp**: `2025-08-07 00:03:48`, `2025-08-07 00:15:35`, `2025-08-07 02:14:35`, `2025-08-08 03:51:05`
- **updated_timestamp**: `2025-08-07 00:03:48`, `2025-08-07T10:15:35.347188`, `2025-08-07T12:14:35.673159`, `2025-08-07T12:14:35.704903`, `2025-08-07T12:14:35.973863`, `2025-08-07T12:14:35.985018`, `2025-08-08T13:51:05.780272`, `2025-08-08T13:51:05.820327`, `2025-08-08T13:51:05.830211`, `2025-08-08T13:51:05.834463`

**Sample Complete Records:**

**Record 1:**
  - `metadata_key`: schema_version
  - `metadata_value`: 2.0
  - `metadata_category`: schema
  - `description`: Enhanced database schema version
  - `created_timestamp`: 2025-08-07 00:03:48
  - `updated_timestamp`: 2025-08-07 00:03:48

**Record 2:**
  - `metadata_key`: table_count
  - `metadata_value`: 16
  - `metadata_category`: stats
  - `description`: Total number of tables in enhanced schema
  - `created_timestamp`: 2025-08-07 00:03:48
  - `updated_timestamp`: 2025-08-07 00:03:48

**Record 3:**
  - `metadata_key`: core_tables_count
  - `metadata_value`: 6
  - `metadata_category`: stats
  - `description`: Number of core data tables
  - `created_timestamp`: 2025-08-07 00:03:48
  - `updated_timestamp`: 2025-08-07 00:03:48

---

## Key Data Distributions

Top values for important categorical columns:

### core_workforce_current.Location

- **Brisbane City**: 6,261 records
- **Adelaide**: 6,115 records
- **Parramatta**: 5,942 records
- **Docklands**: 5,608 records
- **Sydney**: 5,542 records
- **Perth**: 5,532 records

### core_skills_taxonomy.Category

- **Information Technology**: 10,681 records
- **Health Care**: 3,737 records
- **Engineering**: 2,203 records
- **Science and Research**: 1,852 records
- **Finance**: 1,625 records
- **Business**: 1,543 records
- **Media and Communications**: 1,432 records
- **Analysis**: 1,267 records
- **Law, Regulation, and Compliance**: 1,135 records
- **Manufacturing and Production**: 1,111 records
- **Design**: 875 records
- **Marketing and Public Relations**: 716 records
- **Transportation, Supply Chain, and Logistics**: 699 records
- **Maintenance, Repair, and Facility Services**: 678 records
- **Architecture and Construction**: 591 records

### core_skills_taxonomy.SkillType

- **Specialized Skill**: 34,500 records
- **Certification**: 3,526 records
- **Common Skill**: 499 records

### core_colleague_positions_history.Employee Number

- **55001939**: 18 records
- **83932743**: 17 records
- **50331076**: 16 records
- **51402440**: 16 records
- **52085782**: 16 records
- **52656470**: 16 records
- **55952140**: 16 records
- **59657178**: 16 records
- **80454993**: 16 records
- **83937849**: 16 records
- **110603207**: 16 records
- **112766196**: 16 records
- **117995556**: 16 records
- **51709743**: 15 records
- **52292364**: 15 records

### core_colleague_positions_history.Position Number

- **50004748**: 208 records
- **50000863**: 205 records
- **50000990**: 205 records
- **50003059**: 205 records
- **50003401**: 205 records
- **50003476**: 205 records
- **50003889**: 205 records
- **50003911**: 205 records
- **50000531**: 204 records
- **50001243**: 204 records
- **50002285**: 204 records
- **50003853**: 204 records
- **50004118**: 204 records
- **50004584**: 204 records
- **50000032**: 203 records

## Database Indexes

Performance indexes for optimized queries:

### analytics_bundle_characteristics table indexes

**idx_analytics_bundle_characteristics_category**
```sql
CREATE INDEX idx_analytics_bundle_characteristics_category ON analytics_bundle_characteristics(dominant_category)
```

**idx_analytics_bundle_characteristics_level**
```sql
CREATE INDEX idx_analytics_bundle_characteristics_level ON analytics_bundle_characteristics(application_level)
```

**idx_analytics_bundle_characteristics_quality**
```sql
CREATE INDEX idx_analytics_bundle_characteristics_quality ON analytics_bundle_characteristics(silhouette_score)
```

**idx_analytics_bundle_characteristics_value**
```sql
CREATE INDEX idx_analytics_bundle_characteristics_value ON analytics_bundle_characteristics(business_value_score)
```

### analytics_job_defining_skills table indexes

**idx_analytics_job_defining_skills_job**
```sql
CREATE INDEX idx_analytics_job_defining_skills_job ON analytics_job_defining_skills(job_profile_id)
```

**idx_analytics_job_defining_skills_rank**
```sql
CREATE INDEX idx_analytics_job_defining_skills_rank ON analytics_job_defining_skills(defining_skill_rank)
```

**idx_analytics_job_defining_skills_skill**
```sql
CREATE INDEX idx_analytics_job_defining_skills_skill ON analytics_job_defining_skills(skill_id)
```

### analytics_job_families table indexes

**idx_analytics_job_families_cluster**
```sql
CREATE INDEX idx_analytics_job_families_cluster ON analytics_job_families(cluster_id)
```

**idx_analytics_job_families_confidence**
```sql
CREATE INDEX idx_analytics_job_families_confidence ON analytics_job_families(cluster_confidence)
```

**idx_analytics_job_families_function**
```sql
CREATE INDEX idx_analytics_job_families_function ON analytics_job_families(job_function)
```

### analytics_job_similarities table indexes

**idx_analytics_job_similarities_algorithm**
```sql
CREATE INDEX idx_analytics_job_similarities_algorithm ON analytics_job_similarities(calculation_algorithm)
```

**idx_analytics_job_similarities_from**
```sql
CREATE INDEX idx_analytics_job_similarities_from ON analytics_job_similarities(job_from, enhanced_similarity_score DESC)
```

**idx_analytics_job_similarities_score**
```sql
CREATE INDEX idx_analytics_job_similarities_score ON analytics_job_similarities(enhanced_similarity_score DESC)
```

**idx_analytics_job_similarities_to**
```sql
CREATE INDEX idx_analytics_job_similarities_to ON analytics_job_similarities(job_to, enhanced_similarity_score DESC)
```

### analytics_movement_patterns table indexes

**idx_analytics_movement_patterns_from**
```sql
CREATE INDEX idx_analytics_movement_patterns_from ON analytics_movement_patterns(from_job_profile_id)
```

**idx_analytics_movement_patterns_month**
```sql
CREATE INDEX idx_analytics_movement_patterns_month ON analytics_movement_patterns(movement_month)
```

**idx_analytics_movement_patterns_to**
```sql
CREATE INDEX idx_analytics_movement_patterns_to ON analytics_movement_patterns(to_job_profile_id)
```

**idx_analytics_movement_patterns_type**
```sql
CREATE INDEX idx_analytics_movement_patterns_type ON analytics_movement_patterns(movement_type)
```

### analytics_skill_bundles table indexes

**idx_analytics_skill_bundles_cluster**
```sql
CREATE INDEX idx_analytics_skill_bundles_cluster ON analytics_skill_bundles(cluster_id)
```

**idx_analytics_skill_bundles_confidence**
```sql
CREATE INDEX idx_analytics_skill_bundles_confidence ON analytics_skill_bundles(bundle_confidence)
```

**idx_analytics_skill_bundles_specialized**
```sql
CREATE INDEX idx_analytics_skill_bundles_specialized ON analytics_skill_bundles(is_specialized)
```

### analytics_skill_demand_trends table indexes

**idx_analytics_skill_demand_trends_cagr_short**
```sql
CREATE INDEX idx_analytics_skill_demand_trends_cagr_short ON analytics_skill_demand_trends(short_term_cagr)
```

**idx_analytics_skill_demand_trends_category**
```sql
CREATE INDEX idx_analytics_skill_demand_trends_category ON analytics_skill_demand_trends(velocity_category)
```

**idx_analytics_skill_demand_trends_confidence**
```sql
CREATE INDEX idx_analytics_skill_demand_trends_confidence ON analytics_skill_demand_trends(trend_confidence)
```

**idx_analytics_skill_demand_trends_direction**
```sql
CREATE INDEX idx_analytics_skill_demand_trends_direction ON analytics_skill_demand_trends(trend_direction)
```

### analytics_skill_rarity table indexes

**idx_analytics_skill_rarity_category**
```sql
CREATE INDEX idx_analytics_skill_rarity_category ON analytics_skill_rarity(rarity_category)
```

**idx_analytics_skill_rarity_defining**
```sql
CREATE INDEX idx_analytics_skill_rarity_defining ON analytics_skill_rarity(is_defining_skill)
```

**idx_analytics_skill_rarity_prevalence**
```sql
CREATE INDEX idx_analytics_skill_rarity_prevalence ON analytics_skill_rarity(prevalence_percentage)
```

### analytics_specialized_skills table indexes

**idx_analytics_specialized_skills_category**
```sql
CREATE INDEX idx_analytics_specialized_skills_category ON analytics_specialized_skills(specialization_category)
```

**idx_analytics_specialized_skills_importance**
```sql
CREATE INDEX idx_analytics_specialized_skills_importance ON analytics_specialized_skills(strategic_importance)
```

**idx_analytics_specialized_skills_lifecycle**
```sql
CREATE INDEX idx_analytics_specialized_skills_lifecycle ON analytics_specialized_skills(skill_lifecycle_stage)
```

**idx_analytics_specialized_skills_prevalence**
```sql
CREATE INDEX idx_analytics_specialized_skills_prevalence ON analytics_specialized_skills(prevalence_percent)
```

### core_colleague_positions_history table indexes

**idx_colleague_positions_employee**
```sql
CREATE INDEX idx_colleague_positions_employee ON core_colleague_positions_history ("Employee Number")
```

**idx_colleague_positions_lookup_key**
```sql
CREATE INDEX idx_colleague_positions_lookup_key ON core_colleague_positions_history ("PosIDLookupKey")
```

**idx_colleague_positions_movement**
```sql
CREATE INDEX idx_colleague_positions_movement ON core_colleague_positions_history ("Employee Number", "Position Number", "Week Ending")
```

**idx_colleague_positions_position**
```sql
CREATE INDEX idx_colleague_positions_position ON core_colleague_positions_history ("Position Number")
```

**idx_colleague_positions_temporal**
```sql
CREATE INDEX idx_colleague_positions_temporal ON core_colleague_positions_history ("Employee Number", "Week Ending")
```

**idx_colleague_positions_week**
```sql
CREATE INDEX idx_colleague_positions_week ON core_colleague_positions_history ("Week Ending")
```

### core_job_architecture table indexes

**idx_core_job_architecture_category**
```sql
CREATE INDEX idx_core_job_architecture_category ON core_job_architecture(JobCategory)
```

**idx_core_job_architecture_function**
```sql
CREATE INDEX idx_core_job_architecture_function ON core_job_architecture(JobFunction)
```

**idx_core_job_architecture_level**
```sql
CREATE INDEX idx_core_job_architecture_level ON core_job_architecture(ManagementLevel)
```

### core_job_skill_requirements table indexes

**idx_core_job_skill_requirements_composite**
```sql
CREATE INDEX idx_core_job_skill_requirements_composite ON core_job_skill_requirements(JobProfileID, Skill_ID)
```

**idx_core_job_skill_requirements_job**
```sql
CREATE INDEX idx_core_job_skill_requirements_job ON core_job_skill_requirements(JobProfileID)
```

**idx_core_job_skill_requirements_skill**
```sql
CREATE INDEX idx_core_job_skill_requirements_skill ON core_job_skill_requirements(Skill_ID)
```

### core_position_timeline table indexes

**idx_core_position_timeline_job**
```sql
CREATE INDEX idx_core_position_timeline_job ON core_position_timeline(JobProfileID)
```

**idx_core_position_timeline_operational**
```sql
CREATE INDEX idx_core_position_timeline_operational ON core_position_timeline(Operational)
```

**idx_core_position_timeline_position**
```sql
CREATE INDEX idx_core_position_timeline_position ON core_position_timeline(Position_Number)
```

**idx_core_position_timeline_week**
```sql
CREATE INDEX idx_core_position_timeline_week ON core_position_timeline(Week_Ending)
```

### core_skills_taxonomy table indexes

**idx_core_skills_taxonomy_category**
```sql
CREATE INDEX idx_core_skills_taxonomy_category ON core_skills_taxonomy(Category)
```

**idx_core_skills_taxonomy_software**
```sql
CREATE INDEX idx_core_skills_taxonomy_software ON core_skills_taxonomy(isSoftware)
```

**idx_core_skills_taxonomy_type**
```sql
CREATE INDEX idx_core_skills_taxonomy_type ON core_skills_taxonomy(SkillType)
```

### core_workforce_current table indexes

**idx_core_workforce_current_job**
```sql
CREATE INDEX idx_core_workforce_current_job ON core_workforce_current(JobProfileID)
```

**idx_core_workforce_current_location**
```sql
CREATE INDEX idx_core_workforce_current_location ON core_workforce_current(Location)
```

**idx_core_workforce_current_org_2**
```sql
CREATE INDEX idx_core_workforce_current_org_2 ON core_workforce_current(ORG_UNIT_NAME_2)
```

**idx_core_workforce_current_position**
```sql
CREATE INDEX idx_core_workforce_current_position ON core_workforce_current(position_number)
```

## Data Distribution Analysis

Key data patterns and distributions across business tables:

### core_job_architecture Distribution

**JobProfile** (20 unique values):

- Cloud Architect - 4: 9 (7.6%)
- Financial Controller - 3: 8 (6.7%)
- Digital Product Manager - 3: 7 (5.9%)
- Payment Systems Analyst - 0: 6 (5.0%)
- Operations Analyst - 5: 6 (5.0%)
- Legal Counsel - 4: 6 (5.0%)
- HR Business Partner - 3: 6 (5.0%)
- Financial Analyst - 0: 6 (5.0%)
- Cybersecurity Analyst - 3: 6 (5.0%)
- Credit Risk Manager - 3: 6 (5.0%)


### core_skills_taxonomy Distribution

**Skill_Name** (20 unique values):

- z/OS: 1 (5.0%)
- xVal: 1 (5.0%)
- watchOS: 1 (5.0%)
- vMix (Software): 1 (5.0%)
- tvOS: 1 (5.0%)
- t-SNE (t-distributed Stochastic Neighbor Embedding): 1 (5.0%)
- spatialNET: 1 (5.0%)
- shRNA: 1 (5.0%)
- qTest: 1 (5.0%)
- phpList: 1 (5.0%)

**Category** (20 unique values):

- Information Technology: 10,681 (29.9%)
- Health Care: 3,737 (10.5%)
- : 3,374 (9.4%)
- Engineering: 2,203 (6.2%)
- Science and Research: 1,852 (5.2%)
- Finance: 1,625 (4.5%)
- Business: 1,543 (4.3%)
- Media and Communications: 1,432 (4.0%)
- Analysis: 1,267 (3.5%)
- Law, Regulation, and Compliance: 1,135 (3.2%)

**SkillType** (3 unique values):

- Specialized Skill: 34,500 (89.6%)
- Certification: 3,526 (9.2%)
- Common Skill: 499 (1.3%)


### core_workforce_current Distribution

**Location** (6 unique values):

- Brisbane City: 6,261 (17.9%)
- Adelaide: 6,115 (17.5%)
- Parramatta: 5,942 (17.0%)
- Docklands: 5,608 (16.0%)
- Sydney: 5,542 (15.8%)
- Perth: 5,532 (15.8%)


### analytics_job_similarities Distribution

**similarity_score** (20 unique values):

- 0.0: 9,896 (8.9%)
- 7.663967247091857e-05: 8,231 (7.4%)
- 7.397394473279966e-05: 7,253 (6.5%)
- 8.885759127063024e-05: 7,226 (6.5%)
- 9.063474309604283e-05: 7,008 (6.3%)
- 7.286322484191678e-05: 6,681 (6.0%)
- 8.086040805627351e-05: 6,263 (5.7%)
- 0.00010329694985210765: 5,668 (5.1%)
- 7.175250495103391e-05: 5,626 (5.1%)
- 7.930540020903749e-05: 5,161 (4.7%)


### core_colleague_positions_history Distribution

**Employee Number** (20 unique values):

- 55001939: 18 (5.7%)
- 83932743: 17 (5.4%)
- 50331076: 16 (5.1%)
- 51402440: 16 (5.1%)
- 52085782: 16 (5.1%)
- 52656470: 16 (5.1%)
- 55952140: 16 (5.1%)
- 59657178: 16 (5.1%)
- 80454993: 16 (5.1%)
- 83937849: 16 (5.1%)

**Position Number** (20 unique values):

- 50004748: 208 (5.1%)
- 50000863: 205 (5.0%)
- 50000990: 205 (5.0%)
- 50003059: 205 (5.0%)
- 50003401: 205 (5.0%)
- 50003476: 205 (5.0%)
- 50003889: 205 (5.0%)
- 50003911: 205 (5.0%)
- 50000531: 204 (5.0%)
- 50001243: 204 (5.0%)


### analytics_movement_patterns Distribution

**movement_count** (4 unique values):

- 1: 24,512 (95.7%)
- 2: 1,064 (4.2%)
- 3: 30 (0.1%)
- 4: 2 (0.0%)


## Common Query Patterns

### 1. Career Pathway Exploration
```sql
-- Find similar roles with high similarity scores
SELECT j2.JobProfile, js.similarity_score, j2.JobFamily
FROM job_similarities js
JOIN jobs j1 ON js.job_from = j1.JobProfileID
JOIN jobs j2 ON js.job_to = j2.JobProfileID
WHERE j1.JobProfileID = 'R0001.1'
  AND js.similarity_score > 0.7
ORDER BY js.similarity_score DESC
LIMIT 10;
```

### 2. Skills Gap Analysis
```sql
-- Compare skills between two jobs
SELECT s.Skill_Name, s.Category,
       source_skills.Skill_Weight as current_weight,
       target_skills.Skill_Weight as target_weight
FROM skills s
LEFT JOIN job_skills source_skills ON s.Skill_ID = source_skills.Skill_ID
  AND source_skills.JobProfileID = 'R0001.1'
LEFT JOIN job_skills target_skills ON s.Skill_ID = target_skills.Skill_ID
  AND target_skills.JobProfileID = 'R0002.1'
WHERE source_skills.Skill_ID IS NOT NULL
   OR target_skills.Skill_ID IS NOT NULL
ORDER BY s.Category, s.Skill_Name;
```

### 3. Organizational Context
```sql
-- Find roles in specific business units
SELECT DISTINCT j.JobProfile, j.JobFamily, COUNT(DISTINCT p."Position Number") as position_count
FROM jobs j
JOIN positions p ON j.JobProfileID = p.JobProfileID
WHERE p.Business_Unit = 'Technology'
GROUP BY j.JobProfileID, j.JobProfile, j.JobFamily
ORDER BY position_count DESC;
```

### 4. Career Pathways (Pre-computed)
```sql
-- Get career pathway options using pre-computed table
SELECT j.JobProfile, cp.similarity_score, cp.career_move_type, cp.difficulty_score
FROM career_pathways cp
JOIN jobs j ON cp.target_job_id = j.JobProfileID
WHERE cp.source_job_id = 'R0001.1'
  AND cp.similarity_score > 0.6
ORDER BY cp.similarity_rank
LIMIT 12;
```

---

## Schema Evolution Notes

- **Version**: Current schema represents production-ready structure
- **Performance**: Optimized for webapp queries with appropriate indexes
- **Scalability**: Handles current data volumes efficiently
- **Future Extensions**: Schema designed for additive changes

## Usage in Development

This comprehensive schema documentation should be used to:
1. **Inform LLMs** about database structure, relationships, and data patterns
2. **Guide query development** for webapp endpoints with performance considerations
3. **Validate data integrity** during pipeline updates and data quality checks
4. **Plan schema evolution** for future requirements and optimizations
5. **Understand business context** through movement analysis and career pathways
6. **Optimize performance** using the query recommendations and size analysis

## Analysis Summary

- **Database Analysis Date**: 2025-08-08 15:23:21
- **Tables Analyzed**: 17
- **Relationships Mapped**: 17
- **Performance Recommendations**: 2
- **Data Quality Checks**: Completeness, duplicates, referential integrity
- **Business Insights**: Movement patterns, career pathways, skill distributions