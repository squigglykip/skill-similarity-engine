PS C:\Users\P729965\OneDrive - nab\Documents\GitHub\skill-similarity-engine> python decay_rate.py
🔍 DIAGNOSING RETENTION ISSUES
============================================================

📊 MOVEMENT DATA ANALYSIS
----------------------------------------
Movement data by year:
 movement_year  total_movements  unique_from_positions  unique_to_positions  non_null_movements
          2020            12963                  11498                11677               12963
          2021            31299                  18000                18089               31299
          2022            39238                  21961                21943               39238
          2023            18176                  12945                13315               18176
          2024            12255                  10863                11120               12255
          2025             7234                   6862                 6903                7234

📊 JOB PROFILE MATCHING ANALYSIS
----------------------------------------
Position-JobProfile mapping:
 total_positions  unique_positions  positions_with_job_profiles  unique_job_profiles_in_positions
           43096             40673                        43096                              1766

Current job architecture:
 total_job_records  unique_job_profiles
              1765                 1765

📊 DETAILED RETENTION ANALYSIS BY YEAR
----------------------------------------
Total positions in mapping: 40,673
Current job profiles: 1,765

Detailed retention analysis:
 year  total_movements  non_null_positions  with_job_profiles  current_job_profiles_only  retention_rate  position_mapping_rate  job_profile_mapping_rate  current_job_filter_rate
 2020            12963               12963               2039                       2039       15.729384                  100.0                 15.729384               100.000000
 2021            31299               31299               5366                       5366       17.144318                  100.0                 17.144318               100.000000
 2022            39238               39238               8845                       8845       22.541924                  100.0                 22.541924               100.000000
 2023            18176               18176               4870                       4868       26.782570                  100.0                 26.793574                99.958932
 2024            12255               12255               4089                       4083       33.317013                  100.0                 33.365973                99.853265
 2025             7234                7234               2346                       2111       29.181642                  100.0                 32.430191                89.982950

📊 SPECIFIC ISSUE IDENTIFICATION
----------------------------------------
2024 vs 2025 Analysis:
  2024 retention: 33.3%
  2025 retention: 29.2%
  2024 total movements: 12,255.0
  2025 total movements: 7,234.0
  🚨 2025 retention is LOWER than 2024 - investigating...
    → Issue: 2025 positions don't map to job profiles
    → Issue: 2025 job profiles are not in current job architecture

📊 RECOMMENDATIONS
----------------------------------------
🚨 CRITICAL: Overall retention is very low (<30%)
   → Consider relaxing job profile filtering
   → Check if position-to-job mapping is incomplete
   → Verify job architecture is up to date
🚨 2025 DATA ISSUE: Recent year has low retention
   → 2025 data may be incomplete
   → Consider excluding partial year data
   → Or adjust recency weighting to account for incomplete data

💡 ALTERNATIVE APPROACHES:
1. Reduce recency decay rate (0.4 → 0.6) for more historical data
2. Include movements to/from historical job profiles
3. Use fuzzy matching for job profile mapping
4. Exclude incomplete years (2025) from analysis
5. Investigate data loading processes for recent periods

🔒 Database connection closed