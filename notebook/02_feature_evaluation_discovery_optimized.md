================================================================================
ENHANCED FEATURE EVALUATION & PREDICTIVE MOVEMENT ANALYSIS
================================================================================
Comprehensive univariate and multivariate analysis to understand career move predictors

🚀 ENHANCED ANALYSIS FEATURES:
   → Expanded feature set (movement, job, org, employment)
   → Comprehensive univariate analysis (single predictors)
   → True multivariate analysis (feature combinations)
   → Memory-efficient processing for large datasets
   → Detailed insights into career move predictors
💾 Memory: 172.0 MB

================================================================================
DATA LOADING AND INVESTIGATION
================================================================================

📋 METHODOLOGY:
--------------------------------------------------

    Loading data with enhanced context:
    1. Load movement data from database
    2. Load job architecture, positions, and workforce context
    3. Enrich movements with full organisational context
    4. Prepare expanded feature set for analysis


🔗 Connecting to database: models/2025-Q3/workforce_intelligence.sqlite
✅ Successfully connected to database: models/2025-Q3/workforce_intelligence.sqlite
📁 Loading movement data from database table: movement_fact
📋 Column name normalization:
✅ Successfully loaded 121,165 records from movement_fact table
📅 Data range: 2020 - 2025
🏢 Loaded workforce context: 43,096 records
🏢 Loaded jobs data: 1,527 job profiles
🏢 Loaded positions data: 43,096 position records
💾 Memory: 353.8 MB

================================================================================
ENHANCED DATA ENRICHMENT
================================================================================

📋 METHODOLOGY:
--------------------------------------------------

    Enhanced data enrichment with expanded context:
    1. Create clean position-to-context mapping
    2. Enrich movements with job architecture
    3. Add organisational context (division, business unit, salary group)
    4. Include employment context (employee group)
    5. Memory-efficient chunked processing


🔄 Enhanced data enrichment with expanded context...
   → Available columns in positions: ['Employee Number', 'Position Number', 'Position Name', 'JobProfileID', 'Division', 'Business_Unit', 'Team', 'SubTeam', 'Function', 'SubFunction', 'Org_Level_8', 'Org_Level_9', 'Org_Level_10', 'Location', 'Rg', 'Cty', 'Employee Group', 'Salary Group', 'Employee Subgroup']
   → Found Division → will map to Division
   → Found Business_Unit → will map to Business_Unit
   → Found Salary Group → will map to Salary_Group
   → Found Employee Group → will map to Employee_Group
   → Position mapping columns: ['Position Number', 'JobProfileID', 'Division', 'Business_Unit', 'Salary_Group', 'Employee_Group']
   → Workforce context columns: ['week_ending', 'position_number', 'position_name', 'employee_number', 'employee_name', 'location', 'region', 'country', 'employee_group', 'salary_group', 'division', 'business_unit', 'team', 'sub_team', 'function', 'sub_function', 'org_level_8', 'org_level_9', 'org_level_10']
   → New columns after workforce merge: {'employee_group'}
   ⚠️  Workforce merge didn't create expected employee_group_workforce column
   → Enhanced position mapping: 40,673 positions with full context
   → Processing 121,165 records in chunks...
✅ Enhanced enriched dataset: 121,165 movement records
💾 Memory: 378.9 MB

================================================================================
ENHANCED FEATURE PREPARATION
================================================================================
🔍 Available features (10):
   → movement_features: ['movement_count', 'avg_days_between']
   → job_architecture_features: ['from_job_function', 'from_job_sub_function', 'from_job_category', 'from_management_level']
   → organisational_features: ['from_division', 'from_business_unit', 'from_salary_group']
   → employment_features: ['from_employee_group']
🎯 Available targets (8):
   → job_architecture_targets: ['to_job_function', 'to_job_sub_function', 'to_job_category', 'to_management_level']
   → organisational_targets: ['to_division', 'to_business_unit', 'to_salary_group']
   → employment_targets: ['to_employee_group']
🔄 Applying enhanced data cleaning...
   → Initial records: 121,165
   → After dropping null JobProfileIDs: 27,555
   → Current job profiles available: 1,527
   → After job profile filtering: 21,349 (removed 6,206)
Data retention by year:
  2020: 13.8%
  2021: 14.6%
  2022: 18.1%
  2023: 17.6%
  2024: 24.5%
  2025: 23.2%
Overall retention: 17.6%
📊 Final dataset for analysis: 21,349 records
🔄 Encoding categorical variables...
   → Encoding movement_count...
   → Encoding avg_days_between...
   → Encoding from_job_function...
   → Encoding from_job_sub_function...
   → Encoding from_job_category...
   → Encoding from_management_level...
   → Encoding from_division...
   → Encoding from_business_unit...
   → Encoding from_salary_group...
   → Encoding from_employee_group...
   → Encoding to_job_function...
   → Encoding to_job_sub_function...
   → Encoding to_job_category...
   → Encoding to_management_level...
   → Encoding to_division...
   → Encoding to_business_unit...
   → Encoding to_salary_group...
   → Encoding to_employee_group...
💾 Memory: 392.6 MB

================================================================================
COMPREHENSIVE UNIVARIATE ANALYSIS
================================================================================

📋 METHODOLOGY:
--------------------------------------------------

    Univariate analysis tests each feature individually as a predictor:
    1. Single feature → single target predictions
    2. Mutual information scores for feature importance
    3. Chi-square tests for statistical significance
    4. Individual algorithm performance per feature
    5. Feature ranking by predictive power

    This helps identify which single factors are most predictive of career moves.



🎯 UNIVARIATE ANALYSIS FOR: to_job_function
Feature                             MI Score     Chi²         Accuracy     Status
-------------------------------------------------------------------------------------
movement_count                      0.0000      161.92      0.184      ❌ POOR
avg_days_between                    0.0006      2670.59      0.186      ❌ POOR
from_job_function                   1.3329      198884.39      0.698      ✅ GOOD
from_job_sub_function               1.3968      210575.95      0.697      ✅ GOOD
from_job_category                   0.5466      33607.71      0.378      ❌ POOR
from_management_level               0.2973      27850.95      0.298      ❌ POOR
from_division                       0.7560      61518.79      0.451      ⚠️ WEAK
from_business_unit                  1.1752      135915.10      0.590      ⚠️ WEAK
from_salary_group                   0.3183      29855.73      0.309      ❌ POOR
from_employee_group                 0.1183      7094.17      0.249      ❌ POOR

🎯 UNIVARIATE ANALYSIS FOR: to_job_sub_function
Feature                             MI Score     Chi²         Accuracy     Status
-------------------------------------------------------------------------------------
movement_count                      0.0022      287.01      0.155      ❌ POOR
avg_days_between                    0.0122      16813.94      0.157      ❌ POOR
from_job_function                   1.4065      212016.44      0.496      ⚠️ WEAK
from_job_sub_function               1.7944      643110.09      0.629      ✅ GOOD
from_job_category                   0.5888      34774.31      0.242      ❌ POOR
from_management_level               0.3884      34682.58      0.249      ❌ POOR
from_division                       0.9021      77878.43      0.384      ❌ POOR
from_business_unit                  1.5122      295109.36      0.518      ⚠️ WEAK
from_salary_group                   0.4110      37892.38      0.258      ❌ POOR
from_employee_group                 0.1718      10192.22      0.237      ❌ POOR

🎯 UNIVARIATE ANALYSIS FOR: to_job_category
Feature                             MI Score     Chi²         Accuracy     Status
-------------------------------------------------------------------------------------
movement_count                      0.0030      26.52      0.388      ❌ POOR
avg_days_between                    0.0013      430.38      0.384      ❌ POOR
from_job_function                   0.5481      33424.58      0.806      ✅ GOOD
from_job_sub_function               0.5687      34359.61      0.805      ✅ GOOD
from_job_category                   0.5225      32853.88      0.806      ✅ GOOD
from_management_level               0.1070      14798.12      0.447      ⚠️ WEAK
from_division                       0.2632      10003.71      0.631      ✅ GOOD
from_business_unit                  0.4578      19904.24      0.744      ✅ GOOD
from_salary_group                   0.1180      15119.88      0.458      ⚠️ WEAK
from_employee_group                 0.0390      1436.15      0.405      ⚠️ WEAK

🎯 UNIVARIATE ANALYSIS FOR: to_management_level
Feature                             MI Score     Chi²         Accuracy     Status
-------------------------------------------------------------------------------------
movement_count                      0.0000      7.49      0.347      ❌ POOR
avg_days_between                    0.0111      888.92      0.351      ❌ POOR
from_job_function                   0.3061      27552.67      0.456      ⚠️ WEAK
from_job_sub_function               0.3900      35167.41      0.501      ⚠️ WEAK
from_job_category                   0.1040      14648.03      0.357      ❌ POOR
from_management_level               0.6157      44819.01      0.606      ✅ GOOD
from_division                       0.1642      11063.02      0.417      ⚠️ WEAK
from_business_unit                  0.3008      24490.21      0.471      ⚠️ WEAK
from_salary_group                   0.6023      44050.67      0.597      ⚠️ WEAK
from_employee_group                 0.1006      5290.40      0.405      ⚠️ WEAK

🎯 UNIVARIATE ANALYSIS FOR: to_division
Feature                             MI Score     Chi²         Accuracy     Status
-------------------------------------------------------------------------------------
movement_count                      0.0000      44.16      0.326      ❌ POOR
avg_days_between                    0.0000      966.68      0.329      ❌ POOR
from_job_function                   0.7404      64608.98      0.666      ✅ GOOD
from_job_sub_function               0.8780      79729.24      0.736      ✅ GOOD
from_job_category                   0.2627      10471.81      0.427      ⚠️ WEAK
from_management_level               0.1486      12791.99      0.427      ⚠️ WEAK
from_division                       0.9741      156337.29      0.832      ✅ GOOD
from_business_unit                  1.0256      166389.63      0.832      ✅ GOOD
from_salary_group                   0.1472      12863.24      0.431      ⚠️ WEAK
from_employee_group                 0.0681      3539.07      0.404      ⚠️ WEAK

🎯 UNIVARIATE ANALYSIS FOR: to_business_unit
Feature                             MI Score     Chi²         Accuracy     Status
-------------------------------------------------------------------------------------
movement_count                      0.0000      271.64      0.138      ❌ POOR
avg_days_between                    0.0088      8803.08      0.138      ❌ POOR
from_job_function                   1.1800      140331.84      0.360      ❌ POOR
from_job_sub_function               1.5008      295478.96      0.452      ⚠️ WEAK
from_job_category                   0.4769      20727.14      0.210      ❌ POOR
from_management_level               0.2865      24934.47      0.175      ❌ POOR
from_division                       1.0281      166270.62      0.308      ❌ POOR
from_business_unit                  1.9134      719309.33      0.672      ✅ GOOD
from_salary_group                   0.3110      50399.78      0.185      ❌ POOR
from_employee_group                 0.1509      13062.83      0.167      ❌ POOR

🎯 UNIVARIATE ANALYSIS FOR: to_salary_group
Feature                             MI Score     Chi²         Accuracy     Status
-------------------------------------------------------------------------------------
movement_count                      0.0026      299.74      0.340      ❌ POOR
avg_days_between                    0.0133      1385.18      0.343      ❌ POOR
from_job_function                   0.3318      29837.56      0.444      ⚠️ WEAK
from_job_sub_function               0.4157      38473.09      0.488      ⚠️ WEAK
from_job_category                   0.1146      14922.90      0.348      ❌ POOR
from_management_level               0.6124      44511.85      0.591      ⚠️ WEAK
from_division                       0.1706      11468.56      0.405      ⚠️ WEAK
from_business_unit                  0.3302      28328.90      0.463      ⚠️ WEAK
from_salary_group                   0.6291      47740.30      0.591      ⚠️ WEAK
from_employee_group                 0.1321      9252.96      0.406      ⚠️ WEAK

🎯 UNIVARIATE ANALYSIS FOR: to_employee_group
Feature                             MI Score     Chi²         Accuracy     Status
-------------------------------------------------------------------------------------
movement_count                      0.0055      304.51      0.848      ✅ GOOD
avg_days_between                    0.0111      2496.86      0.846      ✅ GOOD
from_job_function                   0.1042      6327.27      0.848      ✅ GOOD
from_job_sub_function               0.1232      9309.89      0.848      ✅ GOOD
from_job_category                   0.0355      1299.11      0.848      ✅ GOOD
from_management_level               0.0797      4109.05      0.848      ✅ GOOD
from_division                       0.0653      3153.98      0.848      ✅ GOOD
from_business_unit                  0.1271      11684.96      0.848      ✅ GOOD
from_salary_group                   0.1102      8015.00      0.848      ✅ GOOD
from_employee_group                 0.0960      8096.24      0.849      ✅ GOOD

================================================================================
TRUE MULTIVARIATE ANALYSIS
================================================================================

📋 METHODOLOGY:
--------------------------------------------------

    Multivariate analysis uses multiple features together:
    1. Feature combinations by category (job, org, employment)
    2. Full feature set predictions
    3. Feature selection techniques
    4. Algorithm comparison with multiple inputs
    5. Feature importance analysis

    This reveals how features interact and combine to predict career moves.



🎯 MULTIVARIATE ANALYSIS FOR: to_job_function
Feature Set          Algorithm            Accuracy     Features   Status
--------------------------------------------------------------------------------
Movement Only        Random Forest        0.186      2          ❌ POOR
Movement Only        Gradient Boosting    0.186      2          ❌ POOR
Movement Only        Logistic Regression  0.187      2          ❌ POOR
Movement Only        Extra Trees          0.186      2          ❌ POOR
Job Architecture     Random Forest        0.696      4          ✅ GOOD
Job Architecture     Gradient Boosting    0.693      4          ✅ GOOD
Job Architecture     Logistic Regression  0.544      4          ⚠️ WEAK
Job Architecture     Extra Trees          0.695      4          ✅ GOOD
Organisational       Random Forest        0.616      3          ✅ GOOD
Organisational       Gradient Boosting    0.620      3          ✅ GOOD
Organisational       Logistic Regression  0.405      3          ⚠️ WEAK
Organisational       Extra Trees          0.616      3          ✅ GOOD
Employment           Random Forest        0.249      1          ❌ POOR
Employment           Gradient Boosting    0.249      1          ❌ POOR
Employment           Logistic Regression  0.233      1          ❌ POOR
Employment           Extra Trees          0.249      1          ❌ POOR
Job + Org            Random Forest        0.701      7          ✅ GOOD
Job + Org            Gradient Boosting    0.699      7          ✅ GOOD
Job + Org            Logistic Regression  0.581      7          ⚠️ WEAK
Job + Org            Extra Trees          0.697      7          ✅ GOOD
All Features         Random Forest        0.692      10         ✅ GOOD
All Features         Gradient Boosting    0.698      10         ✅ GOOD
All Features         Logistic Regression  0.582      10         ⚠️ WEAK
All Features         Extra Trees          0.687      10         ✅ GOOD

🎯 MULTIVARIATE ANALYSIS FOR: to_job_sub_function
Feature Set          Algorithm            Accuracy     Features   Status
--------------------------------------------------------------------------------
Movement Only        Random Forest        0.157      2          ❌ POOR
Movement Only        Gradient Boosting    0.156      2          ❌ POOR
Movement Only        Logistic Regression  0.155      2          ❌ POOR
Movement Only        Extra Trees          0.156      2          ❌ POOR
Job Architecture     Random Forest        0.629      4          ✅ GOOD
Job Architecture     Gradient Boosting    0.577      4          ⚠️ WEAK
Job Architecture     Logistic Regression  0.432      4          ⚠️ WEAK
Job Architecture     Extra Trees          0.627      4          ✅ GOOD
Organisational       Random Forest        0.541      3          ⚠️ WEAK
Organisational       Gradient Boosting    0.508      3          ⚠️ WEAK
Organisational       Logistic Regression  0.358      3          ❌ POOR
Organisational       Extra Trees          0.537      3          ⚠️ WEAK
Employment           Random Forest        0.237      1          ❌ POOR
Employment           Gradient Boosting    0.237      1          ❌ POOR
Employment           Logistic Regression  0.233      1          ❌ POOR
Employment           Extra Trees          0.237      1          ❌ POOR
Job + Org            Random Forest        0.636      7          ✅ GOOD
Job + Org            Gradient Boosting    0.429      7          ⚠️ WEAK
Job + Org            Logistic Regression  0.495      7          ⚠️ WEAK
Job + Org            Extra Trees          0.630      7          ✅ GOOD
All Features         Random Forest        0.620      10         ✅ GOOD
All Features         Gradient Boosting    0.016      10         ❌ POOR
All Features         Logistic Regression  0.498      10         ⚠️ WEAK
All Features         Extra Trees          0.614      10         ✅ GOOD

🎯 MULTIVARIATE ANALYSIS FOR: to_job_category
Feature Set          Algorithm            Accuracy     Features   Status
--------------------------------------------------------------------------------
Movement Only        Random Forest        0.385      2          ❌ POOR
Movement Only        Gradient Boosting    0.385      2          ❌ POOR
Movement Only        Logistic Regression  0.388      2          ❌ POOR
Movement Only        Extra Trees          0.385      2          ❌ POOR
Job Architecture     Random Forest        0.802      4          ✅ GOOD
Job Architecture     Gradient Boosting    0.806      4          ✅ GOOD
Job Architecture     Logistic Regression  0.731      4          ✅ GOOD
Job Architecture     Extra Trees          0.801      4          ✅ GOOD
Organisational       Random Forest        0.768      3          ✅ GOOD
Organisational       Gradient Boosting    0.763      3          ✅ GOOD
Organisational       Logistic Regression  0.582      3          ⚠️ WEAK
Organisational       Extra Trees          0.765      3          ✅ GOOD
Employment           Random Forest        0.405      1          ⚠️ WEAK
Employment           Gradient Boosting    0.405      1          ⚠️ WEAK
Employment           Logistic Regression  0.405      1          ⚠️ WEAK
Employment           Extra Trees          0.405      1          ⚠️ WEAK
Job + Org            Random Forest        0.810      7          ✅ GOOD
Job + Org            Gradient Boosting    0.810      7          ✅ GOOD
Job + Org            Logistic Regression  0.723      7          ✅ GOOD
Job + Org            Extra Trees          0.807      7          ✅ GOOD
All Features         Random Forest        0.803      10         ✅ GOOD
All Features         Gradient Boosting    0.811      10         ✅ GOOD
All Features         Logistic Regression  0.730      10         ✅ GOOD
All Features         Extra Trees          0.801      10         ✅ GOOD

🎯 MULTIVARIATE ANALYSIS FOR: to_management_level
Feature Set          Algorithm            Accuracy     Features   Status
--------------------------------------------------------------------------------
Movement Only        Random Forest        0.350      2          ❌ POOR
Movement Only        Gradient Boosting    0.350      2          ❌ POOR
Movement Only        Logistic Regression  0.347      2          ❌ POOR
Movement Only        Extra Trees          0.351      2          ❌ POOR
Job Architecture     Random Forest        0.625      4          ✅ GOOD
Job Architecture     Gradient Boosting    0.628      4          ✅ GOOD
Job Architecture     Logistic Regression  0.607      4          ✅ GOOD
Job Architecture     Extra Trees          0.625      4          ✅ GOOD
Organisational       Random Forest        0.625      3          ✅ GOOD
Organisational       Gradient Boosting    0.620      3          ✅ GOOD
Organisational       Logistic Regression  0.589      3          ⚠️ WEAK
Organisational       Extra Trees          0.627      3          ✅ GOOD
Employment           Random Forest        0.405      1          ⚠️ WEAK
Employment           Gradient Boosting    0.405      1          ⚠️ WEAK
Employment           Logistic Regression  0.347      1          ❌ POOR
Employment           Extra Trees          0.405      1          ⚠️ WEAK
Job + Org            Random Forest        0.639      7          ✅ GOOD
Job + Org            Gradient Boosting    0.634      7          ✅ GOOD
Job + Org            Logistic Regression  0.609      7          ✅ GOOD
Job + Org            Extra Trees          0.637      7          ✅ GOOD
All Features         Random Forest        0.621      10         ✅ GOOD
All Features         Gradient Boosting    0.632      10         ✅ GOOD
All Features         Logistic Regression  0.604      10         ✅ GOOD
All Features         Extra Trees          0.620      10         ✅ GOOD

🎯 MULTIVARIATE ANALYSIS FOR: to_division
Feature Set          Algorithm            Accuracy     Features   Status
--------------------------------------------------------------------------------
Movement Only        Random Forest        0.329      2          ❌ POOR
Movement Only        Gradient Boosting    0.329      2          ❌ POOR
Movement Only        Logistic Regression  0.327      2          ❌ POOR
Movement Only        Extra Trees          0.329      2          ❌ POOR
Job Architecture     Random Forest        0.743      4          ✅ GOOD
Job Architecture     Gradient Boosting    0.741      4          ✅ GOOD
Job Architecture     Logistic Regression  0.479      4          ⚠️ WEAK
Job Architecture     Extra Trees          0.740      4          ✅ GOOD
Organisational       Random Forest        0.830      3          ✅ GOOD
Organisational       Gradient Boosting    0.825      3          ✅ GOOD
Organisational       Logistic Regression  0.677      3          ✅ GOOD
Organisational       Extra Trees          0.830      3          ✅ GOOD
Employment           Random Forest        0.404      1          ⚠️ WEAK
Employment           Gradient Boosting    0.404      1          ⚠️ WEAK
Employment           Logistic Regression  0.402      1          ⚠️ WEAK
Employment           Extra Trees          0.404      1          ⚠️ WEAK
Job + Org            Random Forest        0.828      7          ✅ GOOD
Job + Org            Gradient Boosting    0.829      7          ✅ GOOD
Job + Org            Logistic Regression  0.689      7          ✅ GOOD
Job + Org            Extra Trees          0.825      7          ✅ GOOD
All Features         Random Forest        0.821      10         ✅ GOOD
All Features         Gradient Boosting    0.828      10         ✅ GOOD
All Features         Logistic Regression  0.691      10         ✅ GOOD
All Features         Extra Trees          0.816      10         ✅ GOOD

🎯 MULTIVARIATE ANALYSIS FOR: to_business_unit
Feature Set          Algorithm            Accuracy     Features   Status
--------------------------------------------------------------------------------
Movement Only        Random Forest        0.138      2          ❌ POOR
Movement Only        Gradient Boosting    0.138      2          ❌ POOR
Movement Only        Logistic Regression  0.139      2          ❌ POOR
Movement Only        Extra Trees          0.138      2          ❌ POOR
Job Architecture     Random Forest        0.463      4          ⚠️ WEAK
Job Architecture     Gradient Boosting    0.428      4          ⚠️ WEAK
Job Architecture     Logistic Regression  0.309      4          ❌ POOR
Job Architecture     Extra Trees          0.461      4          ⚠️ WEAK
Organisational       Random Forest        0.670      3          ✅ GOOD
Organisational       Gradient Boosting    0.358      3          ❌ POOR
Organisational       Logistic Regression  0.311      3          ❌ POOR
Organisational       Extra Trees          0.669      3          ✅ GOOD
Employment           Random Forest        0.167      1          ❌ POOR
Employment           Gradient Boosting    0.167      1          ❌ POOR
Employment           Logistic Regression  0.160      1          ❌ POOR
Employment           Extra Trees          0.167      1          ❌ POOR
Job + Org            Random Forest        0.667      7          ✅ GOOD
Job + Org            Gradient Boosting    0.453      7          ⚠️ WEAK
Job + Org            Logistic Regression  0.440      7          ⚠️ WEAK
Job + Org            Extra Trees          0.664      7          ✅ GOOD
All Features         Random Forest        0.650      10         ✅ GOOD
All Features         Gradient Boosting    0.438      10         ⚠️ WEAK
All Features         Logistic Regression  0.440      10         ⚠️ WEAK
All Features         Extra Trees          0.643      10         ✅ GOOD

🎯 MULTIVARIATE ANALYSIS FOR: to_salary_group
Feature Set          Algorithm            Accuracy     Features   Status
--------------------------------------------------------------------------------
Movement Only        Random Forest        0.343      2          ❌ POOR
Movement Only        Gradient Boosting    0.343      2          ❌ POOR
Movement Only        Logistic Regression  0.340      2          ❌ POOR
Movement Only        Extra Trees          0.343      2          ❌ POOR
Job Architecture     Random Forest        0.611      4          ✅ GOOD
Job Architecture     Gradient Boosting    0.614      4          ✅ GOOD
Job Architecture     Logistic Regression  0.591      4          ⚠️ WEAK
Job Architecture     Extra Trees          0.612      4          ✅ GOOD
Organisational       Random Forest        0.619      3          ✅ GOOD
Organisational       Gradient Boosting    0.616      3          ✅ GOOD
Organisational       Logistic Regression  0.593      3          ⚠️ WEAK
Organisational       Extra Trees          0.621      3          ✅ GOOD
Employment           Random Forest        0.406      1          ⚠️ WEAK
Employment           Gradient Boosting    0.406      1          ⚠️ WEAK
Employment           Logistic Regression  0.340      1          ❌ POOR
Employment           Extra Trees          0.406      1          ⚠️ WEAK
Job + Org            Random Forest        0.635      7          ✅ GOOD
Job + Org            Gradient Boosting    0.626      7          ✅ GOOD
Job + Org            Logistic Regression  0.604      7          ✅ GOOD
Job + Org            Extra Trees          0.633      7          ✅ GOOD
All Features         Random Forest        0.614      10         ✅ GOOD
All Features         Gradient Boosting    0.627      10         ✅ GOOD
All Features         Logistic Regression  0.602      10         ✅ GOOD
All Features         Extra Trees          0.614      10         ✅ GOOD

🎯 MULTIVARIATE ANALYSIS FOR: to_employee_group
Feature Set          Algorithm            Accuracy     Features   Status
--------------------------------------------------------------------------------
Movement Only        Random Forest        0.846      2          ✅ GOOD
Movement Only        Gradient Boosting    0.846      2          ✅ GOOD
Movement Only        Logistic Regression  0.848      2          ✅ GOOD
Movement Only        Extra Trees          0.846      2          ✅ GOOD
Job Architecture     Random Forest        0.862      4          ✅ GOOD
Job Architecture     Gradient Boosting    0.862      4          ✅ GOOD
Job Architecture     Logistic Regression  0.848      4          ✅ GOOD
Job Architecture     Extra Trees          0.863      4          ✅ GOOD
Organisational       Random Forest        0.872      3          ✅ GOOD
Organisational       Gradient Boosting    0.873      3          ✅ GOOD
Organisational       Logistic Regression  0.852      3          ✅ GOOD
Organisational       Extra Trees          0.872      3          ✅ GOOD
Employment           Random Forest        0.849      1          ✅ GOOD
Employment           Gradient Boosting    0.849      1          ✅ GOOD
Employment           Logistic Regression  0.848      1          ✅ GOOD
Employment           Extra Trees          0.849      1          ✅ GOOD
Job + Org            Random Forest        0.872      7          ✅ GOOD
Job + Org            Gradient Boosting    0.872      7          ✅ GOOD
Job + Org            Logistic Regression  0.854      7          ✅ GOOD
Job + Org            Extra Trees          0.871      7          ✅ GOOD
All Features         Random Forest        0.871      10         ✅ GOOD
All Features         Gradient Boosting    0.874      10         ✅ GOOD
All Features         Logistic Regression  0.869      10         ✅ GOOD
All Features         Extra Trees          0.869      10         ✅ GOOD

================================================================================
COMPREHENSIVE ANALYSIS RESULTS
================================================================================
🔍 TOP UNIVARIATE PREDICTORS:
------------------------------------------------------------
   from_employee_group                 → to_employee_group         Acc: 0.849
   from_salary_group                   → to_employee_group         Acc: 0.848
   movement_count                      → to_employee_group         Acc: 0.848
   from_job_function                   → to_employee_group         Acc: 0.848
   from_job_sub_function               → to_employee_group         Acc: 0.848
   from_job_category                   → to_employee_group         Acc: 0.848
   from_management_level               → to_employee_group         Acc: 0.848
   from_division                       → to_employee_group         Acc: 0.848
   from_business_unit                  → to_employee_group         Acc: 0.848
   avg_days_between                    → to_employee_group         Acc: 0.846

📊 BEST PREDICTORS BY FEATURE CATEGORY:

   🏆 Movement:
      movement_count                 → to_employee_group    Acc: 0.848
      avg_days_between               → to_employee_group    Acc: 0.846
      movement_count                 → to_job_category      Acc: 0.388

   🏆 Job Architecture:
      from_job_function              → to_employee_group    Acc: 0.848
      from_job_sub_function          → to_employee_group    Acc: 0.848
      from_job_category              → to_employee_group    Acc: 0.848

   🏆 Organisational:
      from_salary_group              → to_employee_group    Acc: 0.848
      from_division                  → to_employee_group    Acc: 0.848
      from_business_unit             → to_employee_group    Acc: 0.848

   🏆 Employment:
      from_employee_group            → to_employee_group    Acc: 0.849
      from_employee_group            → to_salary_group      Acc: 0.406
      from_employee_group            → to_job_category      Acc: 0.405

🔍 TOP MULTIVARIATE COMBINATIONS:
--------------------------------------------------------------------------------
   All Features         + Gradient Boosting    → to_employee_group    Acc: 0.874
   Organisational       + Gradient Boosting    → to_employee_group    Acc: 0.873
   Organisational       + Random Forest        → to_employee_group    Acc: 0.872
   Job + Org            + Gradient Boosting    → to_employee_group    Acc: 0.872
   Organisational       + Extra Trees          → to_employee_group    Acc: 0.872
   Job + Org            + Random Forest        → to_employee_group    Acc: 0.872
   Job + Org            + Extra Trees          → to_employee_group    Acc: 0.871
   All Features         + Random Forest        → to_employee_group    Acc: 0.871
   All Features         + Logistic Regression  → to_employee_group    Acc: 0.869
   All Features         + Extra Trees          → to_employee_group    Acc: 0.869

📊 BEST PERFORMANCE BY FEATURE SET:
   Movement Only       : Logistic Regression  Acc: 0.848
   Job Architecture    : Extra Trees          Acc: 0.863
   Organisational      : Gradient Boosting    Acc: 0.873
   Employment          : Random Forest        Acc: 0.849
   Job + Org           : Gradient Boosting    Acc: 0.872
   All Features        : Gradient Boosting    Acc: 0.874

🎯 KEY INSIGHTS:
--------------------------------------------------
   → Best single predictor: from_employee_group → to_employee_group (0.849)
   → Best combination: All Features + Gradient Boosting (0.874)
   → Total feature-target combinations tested: 80
   → Total multivariate combinations tested: 192
💾 Memory: 400.3 MB

🔒 Database connection closed

================================================================================
ENHANCED PREDICTIVE ANALYSIS COMPLETE
================================================================================
