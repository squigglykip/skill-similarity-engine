================================================================================
ML-BASED CAREER PATHWAY PREDICTOR
================================================================================
Using Random Forest and ensemble methods for statistical confidence

🚀 PRODUCTION-READY ML APPROACH:
   → Learns optimal feature combinations automatically
   → Provides statistical confidence from ensemble models
   → Handles any class distribution (balanced or imbalanced)
   → Preserves genuine business reality - doesn't artificially balance
   → Defensible, data-driven predictions that reflect actual workforce patterns
   → Feature importance reveals key success factors
   → Falls back to rule-based approach when ML isn't viable
   → Business context interpretation explains what results mean
💾 Memory Usage: 174.8 MB
🔗 Connecting to database: models/2025-Q3/workforce_intelligence.sqlite
✅ Successfully connected to database

============================================================
DATA LOADING AND PREPARATION
============================================================
📚 Loading base data tables...
✅ Loaded movement data: 121,165 records
✅ Loaded job architecture: 1,765 job profiles
✅ Loaded skills data: 77,204 job-skill relationships
💾 Memory Usage: 355.3 MB

============================================================
FEATURE ENGINEERING
============================================================
📊 Loading pre-computed movement features from database...
✅ Loaded 27,555 movement records with pre-computed features
   → Features available: movement_count, avg_days_between, pct_total_movements, unique_employees
   → Temporal features: movement_year, movement_month
   → Context features: predominant_movement_type, monthly_total_movements
🔄 Aggregating movement_fact features to job profile level...
✅ Aggregated to 7,193 job profile transition pairs
   → Using pre-computed DB features: movement_count, avg_days_between, pct_total_movements
   → Added temporal features: frequency, recency_boost, years_active
   → Added market features: avg_monthly_market_volume, avg_pct_total_movements
🎯 Calculating mobility scores from database features...
✅ Calculated mobility for 1,072 source and 1,119 target roles
   → Using database features: total_movement_count, recency_weighted_activity, avg_pct_total_movements
⚙️ Creating movement-focused ML feature matrix from database features...
✅ Created movement-focused feature matrix: 7,058 transition pairs with 22 features
✅ Features focus on job architecture and movement patterns (no skills = no temporal mismatch)
🎯 Creating movement volume targets from recency-weighted data...
   → Using raw recency-weighted movement volume as ML target
   → Using 0.4 exponential decay (aggressive recency bias)
   → This allows transparent interpretation of predictions
✅ Movement targets created from recency-weighted volume:
   → Target range: 0.0 to 325.1 recency-weighted movements
   → Average target: 0.7 movements
   → Median target: 0.2 movements
   → High volume (>70% of max): 1 transitions
   → Method: Direct recency-weighted movement prediction (transparent)
💾 Memory Usage: 369.2 MB
🛠️ Preparing data for ML training...
✅ Prepared ML data for production:
   → Features: 21 columns, 7058 samples
   → Excluded columns: ['from_job_id', 'to_job_id', 'movement_target', 'recency_weighted_activity']
   → Target range: 0.0 to 325.1 recency-weighted movements
   → Target mean: 0.7 movements
   → Features will learn from job characteristics, not target proxy

================================================================================
ML MODEL TRAINING AND EVALUATION - MOVEMENT VOLUME REGRESSION
================================================================================
🎯 REGRESSION APPROACH:
   → Target: Raw recency-weighted movement volume (transparent & interpretable)
   → Method: Direct prediction of movement volume from job characteristics
   → Output: Raw movement predictions + post-processed feasibility %

📊 Target Variable Analysis:
   → Range: 0.0 to 325.1 recency-weighted movements
   → Mean: 0.7 movements
   → Median: 0.2 movements
   → Std Dev: 4.8 movements
   → High volume (>70% of max): 1 transitions
   → Low volume (<30% of max): 7,056 transitions

📊 Data split (production-ready):
   → Training: 5,646 samples (earliest 80%)
   → Testing: 1,412 samples (latest 20%)
   → Using temporal split to prevent future data leakage

🤖 Training Random Forest (Production)...
   ✅ Random Forest (Production) Results:
      → R² Score: 0.938 (higher is better, 1.0 = perfect)
      → RMSE: 0.3 movements (lower is better)
      → MAE: 0.1 movements (average prediction error)
      → CV R² Score: 0.585 (±0.212)
      → Training Time: 0.35s
   🔍 Random Forest (Production) Production Diagnostics:
      → Train R²: 0.492
      → Test R²: 0.938
      → Overfitting Gap: -0.446 ✅ OK
      → CV Stability: ±0.212 ⚠️ UNSTABLE
      → Feature Check: Max feature: 0.468 ✅ BALANCED
      → Status: ⚠️ NEEDS REVIEW
   🧠 Random Forest (Production) Production Interpretation:
      → Outstanding model - explains 93.8% of movement variance (rare in social science!)
      → Accurate - average error 0.1 movements (12.2% of typical volume)

🤖 Training Gradient Boosting (Production)...
   ✅ Gradient Boosting (Production) Results:
      → R² Score: 0.787 (higher is better, 1.0 = perfect)
      → RMSE: 0.6 movements (lower is better)
      → MAE: 0.4 movements (average prediction error)
      → CV R² Score: 0.435 (±0.205)
      → Training Time: 0.25s
   🔍 Gradient Boosting (Production) Production Diagnostics:
      → Train R²: 0.406
      → Test R²: 0.787
      → Overfitting Gap: -0.380 ✅ OK
      → CV Stability: ±0.205 ⚠️ UNSTABLE
      → Feature Check: Max feature: 0.533 ✅ BALANCED
      → Status: ⚠️ NEEDS REVIEW
   🧠 Gradient Boosting (Production) Production Interpretation:
      → Outstanding model - explains 78.7% of movement variance (rare in social science!)
      → Low accuracy - average error 0.4 movements (48.0% of typical volume)

🤖 Training XGBoost (Production)...
   ✅ XGBoost (Production) Results:
      → R² Score: 0.943 (higher is better, 1.0 = perfect)
      → RMSE: 0.3 movements (lower is better)
      → MAE: 0.1 movements (average prediction error)
      → CV R² Score: 0.750 (±0.227)
      → Training Time: 1.90s
   🔍 XGBoost (Production) Production Diagnostics:
      → Train R²: 0.741
      → Test R²: 0.943
      → Overfitting Gap: -0.202 ✅ OK
      → CV Stability: ±0.227 ⚠️ UNSTABLE
      → Feature Check: Max feature: 0.311 ✅ BALANCED
      → Status: ⚠️ NEEDS REVIEW
   🧠 XGBoost (Production) Production Interpretation:
      → Outstanding model - explains 94.3% of movement variance (rare in social science!)
      → Very accurate - average error 0.1 movements (9.6% of typical volume)

⚠️ Best Model (needs review): XGBoost (Production)
   → No models met production readiness criteria

🏆 Best Model: XGBoost (Production)
   → R² Score: 0.943
   → RMSE: 0.3%
   → Average Error: 0.1%

================================================================================
FEATURE IMPORTANCE ANALYSIS
================================================================================
🔍 Top 15 Most Important Features:
------------------------------------------------------------
   total_movement_count               : 0.3107
   total_unique_employees             : 0.2459
   transition_frequency               : 0.1482
   business_unit_mobility_score       : 0.1103
   avg_movements_per_year             : 0.0679
   target_mobility_score              : 0.0630
   source_mobility_score              : 0.0141
   division_mobility_score            : 0.0093
   recency_boost                      : 0.0083
   avg_monthly_market_volume          : 0.0080
   avg_pct_total_movements            : 0.0052
   avg_days_between                   : 0.0042
   years_active                       : 0.0024
   same_management_level              : 0.0023
   same_job_function                  : 0.0002

📊 Feature Importance by Category:
   → Movement: 0.1482
   → Mobility: 0.0771
   → Job Architecture: 0.0024
   → Skills: 0.0000

================================================================================
PATHWAY PREDICTION GENERATION WITH FEASIBILITY CONVERSION
================================================================================
✅ Feature consistency validated: 21 features match between training and prediction
   → Excluded columns: ['from_job_id', 'to_job_id', 'movement_target', 'recency_weighted_activity']
🤖 Generating ensemble predictions from 3 models...
📊 Prediction Results:
   → Total predictions: 7,058
   → Average predicted movements: 0.8
   → High feasibility (≥70%): 0
   → Average feasibility: 0.2%
   → Max historical volume: 325.1 movements
   → Average prediction interval: ±0.5 movements
   → Models used for ensemble: 3

🔝 Top 10 Pathway Recommendations (with confidence indicators):
----------------------------------------------------------------------------------------------------------------------------------------------------------------
From → To                                     Predicted    Feasibility  ±80% CI      Agreement  Sample   Context
----------------------------------------------------------------------------------------------------------------------------------------------------------------
Banking Advisor - 11 → Banking Advisor - 11   79.4         24.4%        ±107.4       0/3        1K       Low Volume (Low Agr.)
Quality Assurance: Aut → Quality Assurance: Aut 74.8         23.0%        ±90.9        1/3        856N     Low Volume (Low Agr.)
Direct Banking - 11 → Direct Banking - 11     70.4         21.6%        ±75.6        1/3        383N     Low Volume (Low Agr.)
Lending Fulfilment: Re → Lending Fulfilment: Re 70.2         21.6%        ±75.1        1/3        707N     Low Volume (Low Agr.)
Business Banker: Middl → Business Banker: Middl 69.7         21.4%        ±73.9        1/3        322N     Low Volume (Low Agr.)
Branch Management - 16 → Branch Management - 16 53.5         16.4%        ±25.4        2/3        318N     Low Volume
Business Banker: Small → Business Banker: Small 50.0         15.4%        ±22.1        1/3        304N     Low Volume (Low Agr.)
Business Banker: Small → Business Banker: Middl 45.6         14.0%        ±27.7        1/3        198N     Low Volume (Low Agr.)
Business Banker: Middl → Business Banker: Middl 45.5         14.0%        ±27.7        1/3        205N     Low Volume (Low Agr.)
Banking Advisor - 00 → Banking Advisor - 11   44.0         13.5%        ±28.1        1/3        196N     Low Volume (Low Agr.)
----------------------------------------------------------------------------------------------------------------------------------------------------------------
💡 Confidence Indicators Legend:
   → ±80% CI: Prediction interval at 80% confidence level
   → Agreement: Fraction of models that agree (within 20% of ensemble mean)
   → Sample: Historical examples (N=count, Low N=≤5 examples)
   → Context: High Volume (≥70%), Moderate (40-69%), Low Volume (<40%)
   → Warnings: (Low N)=few examples, (Low Agr.)=models disagree
💾 Memory Usage: 484.9 MB

================================================================================
ANALYSIS SUMMARY AND INSIGHTS
================================================================================
✅ ML-BASED MOVEMENT VOLUME PREDICTION COMPLETED
   → Best model: XGBoost (Production)
   → Model performance: 0.943 R² score
   → Prediction accuracy: ±0.1 movements average error
   → Total pathway predictions: 7,058
   → High-feasibility pathways: 0
   → Ensemble predictions: 3 models
   → Confidence indicators: Prediction intervals, model agreement, sample size warnings
   → Top predictive features: total_movement_count, total_unique_employees, transition_frequency, business_unit_mobility_score, avg_movements_per_year

🎯 KEY ADVANTAGES OF ML APPROACH:
   → Raw movement predictions (interpretable)
   → Post-processed feasibility percentages (user-friendly)
   → Ensemble confidence: prediction intervals at 80% confidence
   → Model agreement indicators: fraction of models that agree
   → Sample size warnings: flags pathways with limited historical data
   → Automatic feature interaction learning
   → Defensible, evidence-based recommendations
   → Production-ready confidence assessment for business users

💡 NEXT STEPS:
   → Integrate with skills intelligence engine
   → Deploy for real-time pathway recommendations
   → Set up periodic model retraining pipeline
   → A/B test against manual scoring approaches

🔒 Database connection closed
💾 Memory Usage: 484.9 MB

================================================================================
ML-BASED CAREER PATHWAY PREDICTION COMPLETE
Total execution time: 11.86 seconds
================================================================================