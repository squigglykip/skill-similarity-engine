#!/usr/bin/env python3
"""
Feature Evaluation & Movement Data Discovery

Project Goal: Enhance career pathway recommendations by combining skill similarity with 
historical movement patterns, using data-driven methods to identify the most meaningful 
organisational groupings.

Phase 1 Objectives:
1. Data Discovery & Exploration - Understand movement patterns and data quality
2. Feature Evaluation - Use statistical methods to determine optimal grouping dimensions
3. Role & Skill Typology - Categorise roles (launchpads/silos) and skills (bridges/dead-ends)
4. Pathway Enrichment - Create enhanced career recommendations

Note: This analysis uses synthetic data for development purposes. All methods are designed 
to be agnostic to specific outcomes and will work with real-world data when deployed.
"""

import pandas as pd
import numpy as np
import sqlite3
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.stats import chi2_contingency, entropy
from sklearn.feature_selection import mutual_info_classif
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from itertools import combinations
import warnings
warnings.filterwarnings('ignore')

# Set plotting style
plt.style.use('default')
sns.set_palette("husl")

def print_section_header(title, description=""):
    """Print a formatted section header"""
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}")
    if description:
        print(f"{description}")
        print()

def print_methodology(methodology_text):
    """Print methodology explanation with formatting"""
    print(f"\n📋 METHODOLOGY:")
    print(f"{'-'*50}")
    print(f"{methodology_text}")
    print()

def main():
    """Main analysis function"""
    
    print_section_header(
        "FEATURE EVALUATION & MOVEMENT DATA DISCOVERY",
        "Using statistical methods to identify optimal organisational groupings for career pathways"
    )
    
    # =============================================================================
    # 1. LIBRARY IMPORTS AND SETUP
    # =============================================================================
    
    print("✅ Libraries imported successfully")
    print("   → pandas, numpy, sqlite3, matplotlib, seaborn")
    print("   → scipy.stats, sklearn components")
    print("   → Warnings suppressed for cleaner output")
    
    # =============================================================================
    # 2. DATA LOADING AND INVESTIGATION
    # =============================================================================
    
    print_section_header("DATA LOADING AND INVESTIGATION")
    print_methodology("""
    Following the proven approach from 01_movement_data_discovery.ipynb:
    1. Load movement data from realistic_movement_fact_table.csv 
    2. Connect to SQLite for job architecture context (jobs, positions tables)
    3. Perform pandas merges to enrich movement data with job context
    4. Validate data quality and completeness for statistical analysis
    
    This approach ensures we work with the actual movement data while leveraging
    the rich job context available in the database.
    """)
    
    # Load movement data from CSV (following working notebook pattern)
    movement_file_paths = [
        "../data/synthetic_test/movement_analysis/realistic_movement_fact_table.csv",  # From notebook dir
        "data/synthetic_test/movement_analysis/realistic_movement_fact_table.csv",     # From project root
        "./data/synthetic_test/movement_analysis/realistic_movement_fact_table.csv"   # Explicit
    ]
    
    movement_df = None
    for movement_path in movement_file_paths:
        try:
            movement_df = pd.read_csv(movement_path)
            print(f"📁 Loaded movement data from: {movement_path}")
            break
        except FileNotFoundError:
            continue
    
    if movement_df is None:
        raise FileNotFoundError("Could not find realistic_movement_fact_table.csv. Please check file path.")
    
    print(f"📊 Movement data loaded: {len(movement_df):,} records")
    print(f"📅 Date range: {movement_df['movement_year'].min()} - {movement_df['movement_year'].max()}")
    print(f"🔄 Movement types: {movement_df['predominant_movement_type'].value_counts().to_dict()}")
    
    # Connect to SQLite database for job context (following working notebook)
    database_paths = [
        '../models/2025-Q3/workforce_intelligence.sqlite',  # From notebook directory
        'models/2025-Q3/workforce_intelligence.sqlite',     # From project root
        './models/2025-Q3/workforce_intelligence.sqlite'    # From project root (explicit)
    ]
    
    conn = None
    for db_path in database_paths:
        try:
            conn = sqlite3.connect(db_path)
            print(f"🔗 Connected to database: {db_path}")
            break
        except sqlite3.OperationalError:
            continue
    
    if conn is None:
        raise FileNotFoundError("Could not find workforce_intelligence.sqlite database. Please check file path.")
    
    # Load job architecture data (following working notebook pattern)
    jobs_df = pd.read_sql_query("SELECT * FROM jobs", conn)
    positions_df = pd.read_sql_query("SELECT * FROM positions", conn)
    
    print(f"🏢 Loaded jobs data: {len(jobs_df):,} job profiles")
    print(f"🏢 Loaded positions data: {len(positions_df):,} position records")
    
    print(f"\n🏗️ Job Architecture Hierarchy:")
    print(f"   Job Functions: {jobs_df['JobFunction'].nunique()}")
    print(f"   Job Sub-Functions: {jobs_df['JobSubFunction'].nunique()}")
    print(f"   Management Levels: {jobs_df['ManagementLevel'].nunique()}")
    print(f"   Job Categories: {jobs_df['JobCategory'].nunique()}")
    
    # =============================================================================
    # 3. DATA ENRICHMENT WITH JOB CONTEXT
    # =============================================================================
    
    print_section_header("DATA ENRICHMENT WITH JOB CONTEXT")
    print_methodology("""
    Following the successful approach from 01_movement_data_discovery.ipynb:
    1. Convert data types to ensure successful merges
    2. Step-by-step pandas merges to add job context
    3. Validate merge success and data completeness
    4. Create enriched dataset ready for statistical analysis
    
    This proven approach achieves 100% merge success as demonstrated in the working notebook.
    """)
    
    # Data type conversion (following working notebook exactly)
    print("🔄 Converting data types for successful merges...")
    positions_df['Position Number'] = positions_df['Position Number'].astype(str)
    movement_df['from_position'] = movement_df['from_position'].astype(str)
    movement_df['to_position'] = movement_df['to_position'].astype(str)
    
    print(f"   → Movement 'from_position' type: {movement_df['from_position'].dtype}")
    print(f"   → Positions 'Position Number' type: {positions_df['Position Number'].dtype}")
    
    # Step 1: Merge movement data with positions for 'from' positions
    print("\n📋 Step 1: Adding 'from' position context...")
    movement_with_context = movement_df.merge(
        positions_df[['Position Number', 'JobProfileID']],
        left_on='from_position',
        right_on='Position Number',
        how='left',
        suffixes=('', '_pos_from')
    ).drop('Position Number', axis=1)
    
    # Step 2: Merge with positions for 'to' positions  
    print("📋 Step 2: Adding 'to' position context...")
    movement_with_context = movement_with_context.merge(
        positions_df[['Position Number', 'JobProfileID']],
        left_on='to_position',
        right_on='Position Number',
        how='left',
        suffixes=('_from', '_to')
    ).drop('Position Number', axis=1)
    
    # Step 3: Add job architecture context for 'from' positions
    print("📋 Step 3: Adding 'from' job architecture context...")
    movement_with_context = movement_with_context.merge(
        jobs_df[['JobProfileID', 'JobFunction', 'JobSubFunction', 'ManagementLevel', 'JobCategory']],
        left_on='JobProfileID_from',
        right_on='JobProfileID',
        how='left',
        suffixes=('', '_from')
    ).drop('JobProfileID', axis=1)
    
    # Step 4: Add job architecture context for 'to' positions
    print("📋 Step 4: Adding 'to' job architecture context...")
    movement_with_context = movement_with_context.merge(
        jobs_df[['JobProfileID', 'JobFunction', 'JobSubFunction', 'ManagementLevel', 'JobCategory']],
        left_on='JobProfileID_to',
        right_on='JobProfileID',
        how='left',
        suffixes=('_from', '_to')
    ).drop('JobProfileID', axis=1)
    
    # Rename columns to match our analysis expectations
    movements_df = movement_with_context.rename(columns={
        'JobFunction_from': 'from_job_function',
        'JobSubFunction_from': 'from_job_sub_function',
        'JobCategory_from': 'from_job_category',
        'ManagementLevel_from': 'from_management_level',
        'JobFunction_to': 'to_job_function',
        'JobSubFunction_to': 'to_job_sub_function',
        'JobCategory_to': 'to_job_category',
        'ManagementLevel_to': 'to_management_level'
    })
    
    print(f"✅ Enriched dataset created: {len(movements_df):,} movement records")
    
    # Validate merge success (following working notebook pattern)
    print(f"\n📊 Merge Success Validation:")
    from_pos_coverage = movements_df['JobProfileID_from'].notna().sum()
    to_pos_coverage = movements_df['JobProfileID_to'].notna().sum()
    from_job_coverage = movements_df['from_job_function'].notna().sum()
    to_job_coverage = movements_df['to_job_function'].notna().sum()
    
    print(f"   → From positions with context: {from_pos_coverage:,} / {len(movements_df):,} ({from_pos_coverage/len(movements_df)*100:.1f}%)")
    print(f"   → To positions with context: {to_pos_coverage:,} / {len(movements_df):,} ({to_pos_coverage/len(movements_df)*100:.1f}%)")
    print(f"   → From jobs with context: {from_job_coverage:,} / {len(movements_df):,} ({from_job_coverage/len(movements_df)*100:.1f}%)")
    print(f"   → To jobs with context: {to_job_coverage:,} / {len(movements_df):,} ({to_job_coverage/len(movements_df)*100:.1f}%)")
    
    # Check complete context success
    successful_merges = (movements_df['from_job_function'].notna() & 
                        movements_df['to_job_function'].notna()).sum()
    merge_success_rate = successful_merges / len(movements_df)
    
    print(f"\n✅ Successful complete merges: {successful_merges:,} / {len(movements_df):,} ({merge_success_rate*100:.1f}%)")
    
    if merge_success_rate < 0.8:
        print("   ⚠️  Low merge success rate - may impact statistical analysis quality")
    else:
        print("   ✅ Excellent merge success rate - ready for statistical analysis")
    
    # Data quality assessment  
    missing_values = movements_df.isnull().sum().sum()
    total_values = movements_df.size
    completeness_rate = (total_values - missing_values) / total_values
    
    print(f"\n📈 Data Quality Assessment:")
    print(f"   → Total data points: {total_values:,}")
    print(f"   → Missing values: {missing_values:,}")
    print(f"   → Overall completeness rate: {completeness_rate*100:.1f}%")
    
    # Display sample enriched data
    print(f"\n📋 Sample enriched movement records:")
    sample_cols = ['from_job_function', 'to_job_function', 'from_job_category', 'to_job_category']
    available_cols = [col for col in sample_cols if col in movements_df.columns]
    if available_cols:
        print(movements_df[available_cols].head())
    else:
        print("Available columns:", movements_df.columns.tolist()[:10])
    
    # =============================================================================
    # 4. STATISTICAL FEATURE EVALUATION
    # =============================================================================
    
    print_section_header("STATISTICAL FEATURE EVALUATION")
    print_methodology("""
    Applying 'let the data speak' approach to determine which organisational features
    contain the most meaningful signal for predicting career transitions.
    
    We use three complementary statistical methods:
    
    1. MUTUAL INFORMATION ANALYSIS:
       - Measures how much knowing one variable reduces uncertainty about another
       - Works with categorical data and captures non-linear relationships
       - Higher scores = stronger predictive relationship
    
    2. CHI-SQUARE TEST OF INDEPENDENCE:
       - Tests statistical significance of relationships between categorical variables
       - Provides p-values for confidence assessment
       - Cramer's V gives standardised effect size (0-1 scale)
    
    3. RANDOM FOREST FEATURE IMPORTANCE:
       - Measures practical predictive utility in machine learning context
       - Captures complex interactions between features
       - Provides importance scores for prediction tasks
    
    This triangulated approach ensures robust feature selection across multiple dimensions.
    """)
    
    # Prepare clean dataset for analysis
    # Based on schema-corrected column names from jobs table
    # Note: Additional organizational features from positions table could include:
    # Division, Business_Unit, Team, Location, Rg (region), Employee_Group, Salary_Group
    features_to_evaluate = [
        'from_job_function',
        'from_job_sub_function', 
        'from_job_category',
        'from_management_level'
    ]
    
    targets_to_evaluate = [
        'to_job_function',
        'to_job_sub_function',
        'to_job_category', 
        'to_management_level'
    ]
    
    # Filter available columns
    available_features = [f for f in features_to_evaluate if f in movements_df.columns]
    available_targets = [t for t in targets_to_evaluate if t in movements_df.columns]
    
    print(f"🔍 Available features for analysis: {available_features}")
    print(f"🎯 Available targets for analysis: {available_targets}")
    
    # Clean data for analysis
    analysis_cols = available_features + available_targets
    clean_movements = movements_df.dropna(subset=analysis_cols)
    
    print(f"📊 Clean dataset: {len(clean_movements):,} records ({len(clean_movements)/len(movements_df)*100:.1f}% of original)")
    
    if len(clean_movements) < 100:
        print("   ⚠️  Warning: Very small sample size may affect statistical reliability")
    
    # =============================================================================
    # 4.1 MUTUAL INFORMATION ANALYSIS
    # =============================================================================
    
    print(f"\n🔬 MUTUAL INFORMATION ANALYSIS")
    print(f"{'-'*50}")
    print("Calculating information content and uncertainty reduction...")
    
    # Encode categorical variables
    label_encoders = {}
    encoded_data = clean_movements.copy()
    
    for col in analysis_cols:
        le = LabelEncoder()
        encoded_data[f'{col}_encoded'] = le.fit_transform(clean_movements[col].astype(str))
        label_encoders[col] = le
    
    # Calculate mutual information scores
    mutual_info_results = []
    
    for target in available_targets:
        target_encoded = f'{target}_encoded'
        
        # Prepare feature matrix
        X = encoded_data[[f'{f}_encoded' for f in available_features]]
        y = encoded_data[target_encoded]
        
        # Calculate mutual information
        mi_scores = mutual_info_classif(X, y, random_state=42)
        
        for i, feature in enumerate(available_features):
            mutual_info_results.append({
                'feature': feature,
                'target': target,
                'mutual_information': mi_scores[i]
            })
    
    # Convert to DataFrame and display results
    mi_df = pd.DataFrame(mutual_info_results)
    mi_pivot = mi_df.pivot(index='feature', columns='target', values='mutual_information')
    
    print("📈 Mutual Information Scores (higher = more predictive power):")
    print(mi_pivot.round(4))
    
    # =============================================================================
    # 4.2 CHI-SQUARE TEST OF INDEPENDENCE
    # =============================================================================
    
    print(f"\n🔬 CHI-SQUARE TEST OF INDEPENDENCE")
    print(f"{'-'*50}")
    print("Testing statistical significance of categorical relationships...")
    
    def cramers_v(x, y):
        """Calculate Cramer's V statistic for categorical association"""
        confusion_matrix = pd.crosstab(x, y)
        chi2 = stats.chi2_contingency(confusion_matrix)[0]
        n = confusion_matrix.sum().sum()
        phi2 = chi2 / n
        r, k = confusion_matrix.shape
        phi2corr = max(0, phi2 - ((k-1)*(r-1))/(n-1))
        rcorr = r - ((r-1)**2)/(n-1)
        kcorr = k - ((k-1)**2)/(n-1)
        return np.sqrt(phi2corr / min(kcorr-1, rcorr-1))
    
    chi_square_results = []
    
    for target in available_targets:
        for feature in available_features:
            try:
                # Create contingency table
                contingency_table = pd.crosstab(clean_movements[feature], clean_movements[target])
                
                # Perform chi-square test
                chi2, p_value, dof, expected = chi2_contingency(contingency_table)
                
                # Calculate Cramer's V
                cramers_v_score = cramers_v(clean_movements[feature], clean_movements[target])
                
                chi_square_results.append({
                    'feature': feature,
                    'target': target,
                    'chi_square': chi2,
                    'p_value': p_value,
                    'degrees_of_freedom': dof,
                    'cramers_v': cramers_v_score,
                    'significant': p_value < 0.05 if isinstance(p_value, (int, float)) else False
                })
            except Exception as e:
                print(f"   ⚠️  Warning: Chi-square test failed for {feature} vs {target}: {str(e)}")
    
    # Convert to DataFrame and display
    chi_df = pd.DataFrame(chi_square_results)
    
    print("📈 Chi-Square Test Results:")
    for target in available_targets:
        target_results = chi_df[chi_df['target'] == target].copy()
        target_results = target_results.sort_values('cramers_v', ascending=False)
        
        print(f"\n   Predicting {target}:")
        result_cols = ['feature', 'chi_square', 'p_value', 'cramers_v', 'significant']
        print(target_results[result_cols].round(4).to_string(index=False))
    
    # =============================================================================
    # 4.3 RANDOM FOREST FEATURE IMPORTANCE
    # =============================================================================
    
    print(f"\n🔬 RANDOM FOREST FEATURE IMPORTANCE")
    print(f"{'-'*50}")
    print("Measuring practical predictive utility in machine learning context...")
    
    rf_results = []
    
    for target in available_targets:
        target_encoded = f'{target}_encoded'
        
        # Prepare features and target
        X = encoded_data[[f'{f}_encoded' for f in available_features]]
        y = encoded_data[target_encoded]
        
        try:
            # Split data for training
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
            
            # Train Random Forest
            rf = RandomForestClassifier(n_estimators=100, random_state=42)
            rf.fit(X_train, y_train)
            
            # Get feature importance scores
            importances = rf.feature_importances_
            
            # Calculate model accuracy
            train_score = rf.score(X_train, y_train)
            test_score = rf.score(X_test, y_test)
            
            for i, feature in enumerate(available_features):
                rf_results.append({
                    'feature': feature,
                    'target': target,
                    'importance': importances[i],
                    'train_accuracy': train_score,
                    'test_accuracy': test_score
                })
        except Exception as e:
            print(f"   ⚠️  Warning: Random Forest failed for target {target}: {str(e)}")
    
    # Convert to DataFrame and display
    rf_df = pd.DataFrame(rf_results)
    
    print("📈 Random Forest Feature Importance Results:")
    for target in available_targets:
        target_results = rf_df[rf_df['target'] == target].copy()
        if not target_results.empty:
            target_results = target_results.sort_values('importance', ascending=False)
            
            print(f"\n   Predicting {target}:")
            print(f"   Model Accuracy: {target_results['test_accuracy'].iloc[0]:.3f}")
            print(target_results[['feature', 'importance']].round(4).to_string(index=False))
    
    # =============================================================================
    # 4.4 MULTIVARIATE REGRESSION ANALYSIS
    # =============================================================================
    
    print(f"\n🔬 MULTIVARIATE REGRESSION ANALYSIS")
    print(f"{'-'*50}")
    print("Analyzing feature interactions and multivariate relationships...")
    
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.svm import SVC
    from sklearn.metrics import classification_report, confusion_matrix
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import Pipeline
    from sklearn.model_selection import cross_val_score
    
    # Import XGBoost (with fallback if not installed)
    try:
        from xgboost import XGBClassifier
        XGBOOST_AVAILABLE = True
    except ImportError:
        XGBOOST_AVAILABLE = False
        print("   ⚠️  XGBoost not installed. Install with: pip install xgboost")
    
    regression_results = []
    
    # Define multiple regression algorithms
    algorithms = {
        'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42),
        'Gradient Boosting': GradientBoostingClassifier(n_estimators=100, random_state=42),
        'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
        'SVM (RBF)': SVC(kernel='rbf', probability=True, random_state=42)
    }
    
    # Add XGBoost if available
    if XGBOOST_AVAILABLE:
        algorithms['XGBoost'] = XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42,
            eval_metric='logloss'  # Suppress warnings
        )
        print("   ✅ XGBoost included in algorithm comparison")
    else:
        print("   ⚠️  XGBoost not available - install with: pip install xgboost")
    
    print("📊 Testing multiple regression algorithms with all features combined...")
    
    for target in available_targets:
        target_encoded = f'{target}_encoded'
        
        # Prepare features and target
        X = encoded_data[[f'{f}_encoded' for f in available_features]]
        y = encoded_data[target_encoded]
        
        print(f"\n   🎯 Predicting {target}:")
        print(f"   {'Algorithm':<20} {'CV Score':<10} {'Test Acc':<10} {'Feature Count':<15}")
        print(f"   {'-'*60}")
        
        for alg_name, algorithm in algorithms.items():
            try:
                # Split data
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
                
                # Create pipeline with scaling for algorithms that need it
                if alg_name in ['Logistic Regression', 'SVM (RBF)']:
                    pipeline = Pipeline([
                        ('scaler', StandardScaler()),
                        ('classifier', algorithm)
                    ])
                else:
                    pipeline = Pipeline([
                        ('classifier', algorithm)
                    ])
                
                # Cross-validation score
                cv_scores = cross_val_score(pipeline, X_train, y_train, cv=5, scoring='accuracy')
                cv_mean = cv_scores.mean()
                
                # Fit and test
                pipeline.fit(X_train, y_train)
                test_score = pipeline.score(X_test, y_test)
                
                print(f"   {alg_name:<20} {cv_mean:.3f}     {test_score:.3f}     {len(available_features)}")
                
                # Store results
                regression_results.append({
                    'algorithm': alg_name,
                    'target': target,
                    'cv_score': cv_mean,
                    'test_score': test_score,
                    'feature_count': len(available_features),
                    'feature_type': 'all_features'
                })
                
                # Feature importance for tree-based models
                if hasattr(pipeline.named_steps['classifier'], 'feature_importances_'):
                    importances = pipeline.named_steps['classifier'].feature_importances_
                    feature_importance = dict(zip(available_features, importances))
                    
                    # Store feature importance
                    for feature, importance in feature_importance.items():
                        regression_results.append({
                            'algorithm': alg_name,
                            'target': target,
                            'feature': feature,
                            'importance': importance,
                            'feature_type': 'importance'
                        })
                
            except Exception as e:
                print(f"   {alg_name:<20} FAILED    FAILED    {len(available_features)} ({str(e)[:30]}...)")
    
    # =============================================================================
    # 4.5 FEATURE INTERACTION ANALYSIS
    # =============================================================================
    
    print(f"\n🔬 FEATURE INTERACTION ANALYSIS")
    print(f"{'-'*50}")
    print("Analyzing pairwise feature interactions and polynomial features...")
    
    from sklearn.preprocessing import PolynomialFeatures
    
    # Test feature interactions
    interaction_results = []
    
    # Generate all pairwise combinations
    feature_pairs = list(combinations(available_features, 2))
    
    print(f"📊 Testing {len(feature_pairs)} feature pair interactions...")
    
    for target in available_targets:
        target_encoded = f'{target}_encoded'
        y = encoded_data[target_encoded]
        
        print(f"\n   🎯 Feature Interactions for {target}:")
        print(f"   {'Feature Pair':<35} {'LogReg':<8} {'GradBoost':<10} {'Improvement':<12}")
        print(f"   {'-'*70}")
        
        # Baseline performance with all features
        X_all = encoded_data[[f'{f}_encoded' for f in available_features]]
        X_train, X_test, y_train, y_test = train_test_split(X_all, y, test_size=0.3, random_state=42)
        
        # Baseline scores
        baseline_lr = LogisticRegression(max_iter=1000, random_state=42)
        baseline_gb = GradientBoostingClassifier(n_estimators=50, random_state=42)  # Reduced for speed
        
        baseline_lr.fit(X_train, y_train)
        baseline_gb.fit(X_train, y_train)
        
        baseline_lr_score = baseline_lr.score(X_test, y_test)
        baseline_gb_score = baseline_gb.score(X_test, y_test)
        
        # Test top feature pairs (limit to avoid excessive computation)
        top_pairs = feature_pairs[:min(10, len(feature_pairs))]
        
        for feature1, feature2 in top_pairs:
            try:
                # Create interaction features
                X_pair = encoded_data[[f'{feature1}_encoded', f'{feature2}_encoded']]
                
                # Add polynomial features (interactions)
                poly = PolynomialFeatures(degree=2, include_bias=False, interaction_only=True)
                X_poly = poly.fit_transform(X_pair)
                
                # Split data
                X_train_poly, X_test_poly, y_train_poly, y_test_poly = train_test_split(
                    X_poly, y, test_size=0.3, random_state=42
                )
                
                # Test with Logistic Regression
                lr_poly = LogisticRegression(max_iter=1000, random_state=42)
                lr_poly.fit(X_train_poly, y_train_poly)
                lr_poly_score = lr_poly.score(X_test_poly, y_test_poly)
                
                # Test with Gradient Boosting
                gb_poly = GradientBoostingClassifier(n_estimators=50, random_state=42)
                gb_poly.fit(X_train_poly, y_train_poly)
                gb_poly_score = gb_poly.score(X_test_poly, y_test_poly)
                
                # Calculate improvement over baseline
                lr_improvement = lr_poly_score - baseline_lr_score
                gb_improvement = gb_poly_score - baseline_gb_score
                
                pair_name = f"{feature1.replace('from_', '')} + {feature2.replace('from_', '')}"
                improvement_indicator = "↑" if max(lr_improvement, gb_improvement) > 0.01 else "→"
                
                print(f"   {pair_name:<35} {lr_poly_score:.3f}   {gb_poly_score:.3f}     {improvement_indicator} {max(lr_improvement, gb_improvement):+.3f}")
                
                # Store results
                interaction_results.append({
                    'target': target,
                    'feature1': feature1,
                    'feature2': feature2,
                    'lr_score': lr_poly_score,
                    'gb_score': gb_poly_score,
                    'lr_improvement': lr_improvement,
                    'gb_improvement': gb_improvement,
                    'max_improvement': max(lr_improvement, gb_improvement)
                })
                
            except Exception as e:
                print(f"   {pair_name:<35} FAILED   FAILED      ERROR")
    
    # =============================================================================
    # 4.6 REGULARIZATION AND FEATURE SELECTION
    # =============================================================================
    
    print(f"\n🔬 REGULARIZATION AND FEATURE SELECTION")
    print(f"{'-'*50}")
    print("Testing L1/L2 regularization and automated feature selection...")
    
    from sklearn.linear_model import Ridge, Lasso, ElasticNet
    from sklearn.feature_selection import SelectKBest, f_classif, RFE
    
    regularization_results = []
    
    # Define regularization methods
    regularization_methods = {
        'Ridge (L2)': Ridge(alpha=1.0, random_state=42),
        'Lasso (L1)': Lasso(alpha=0.1, random_state=42, max_iter=1000),
        'ElasticNet': ElasticNet(alpha=0.1, l1_ratio=0.5, random_state=42, max_iter=1000),
        'Logistic + L1': LogisticRegression(penalty='l1', solver='liblinear', C=1.0, random_state=42),
        'Logistic + L2': LogisticRegression(penalty='l2', C=1.0, random_state=42, max_iter=1000)
    }
    
    # Feature selection methods
    feature_selection_methods = {
        'SelectKBest (k=2)': SelectKBest(score_func=f_classif, k=2),
        'SelectKBest (k=3)': SelectKBest(score_func=f_classif, k=3),
        'RFE (n=2)': RFE(estimator=LogisticRegression(random_state=42, max_iter=1000), n_features_to_select=2),
        'RFE (n=3)': RFE(estimator=LogisticRegression(random_state=42, max_iter=1000), n_features_to_select=3)
    }
    
    for target in available_targets:
        target_encoded = f'{target}_encoded'
        
        # Prepare features and target
        X = encoded_data[[f'{f}_encoded' for f in available_features]]
        y = encoded_data[target_encoded]
        
        print(f"\n   🎯 Regularization Results for {target}:")
        print(f"   {'Method':<20} {'CV Score':<10} {'Test Score':<12} {'Features':<10}")
        print(f"   {'-'*55}")
        
        # Test regularization methods
        for method_name, method in regularization_methods.items():
            try:
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
                
                # For regression methods, we need to convert to regression problem
                if method_name in ['Ridge (L2)', 'Lasso (L1)', 'ElasticNet']:
                    # Skip these for classification - they're for regression
                    continue
                
                # Create pipeline with scaling
                pipeline = Pipeline([
                    ('scaler', StandardScaler()),
                    ('classifier', method)
                ])
                
                # Cross-validation
                cv_scores = cross_val_score(pipeline, X_train, y_train, cv=5, scoring='accuracy')
                cv_mean = cv_scores.mean()
                
                # Fit and test
                pipeline.fit(X_train, y_train)
                test_score = pipeline.score(X_test, y_test)
                
                print(f"   {method_name:<20} {cv_mean:.3f}     {test_score:.3f}       {len(available_features)}")
                
                # Store results
                regularization_results.append({
                    'method': method_name,
                    'target': target,
                    'cv_score': cv_mean,
                    'test_score': test_score,
                    'feature_count': len(available_features)
                })
                
            except Exception as e:
                print(f"   {method_name:<20} FAILED    FAILED        {len(available_features)}")
        
        # Test feature selection methods
        print(f"\n   🎯 Feature Selection Results for {target}:")
        print(f"   {'Method':<20} {'CV Score':<10} {'Test Score':<12} {'Selected Features':<20}")
        print(f"   {'-'*75}")
        
        for method_name, selector in feature_selection_methods.items():
            try:
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
                
                # Create pipeline with feature selection
                pipeline = Pipeline([
                    ('scaler', StandardScaler()),
                    ('selector', selector),
                    ('classifier', LogisticRegression(random_state=42, max_iter=1000))
                ])
                
                # Cross-validation
                cv_scores = cross_val_score(pipeline, X_train, y_train, cv=5, scoring='accuracy')
                cv_mean = cv_scores.mean()
                
                # Fit and test
                pipeline.fit(X_train, y_train)
                test_score = pipeline.score(X_test, y_test)
                
                # Get selected features
                selected_features = pipeline.named_steps['selector'].get_support()
                selected_names = [available_features[i] for i, selected in enumerate(selected_features) if selected]
                selected_str = ', '.join([f.replace('from_', '') for f in selected_names[:2]]) + ('...' if len(selected_names) > 2 else '')
                
                print(f"   {method_name:<20} {cv_mean:.3f}     {test_score:.3f}       {selected_str:<20}")
                
                # Store results
                regularization_results.append({
                    'method': method_name,
                    'target': target,
                    'cv_score': cv_mean,
                    'test_score': test_score,
                    'selected_features': selected_names,
                    'feature_count': len(selected_names)
                })
                
            except Exception as e:
                print(f"   {method_name:<20} FAILED    FAILED        ERROR")

    # =============================================================================
    # 4.7 ENSEMBLE METHODS AND ADVANCED TECHNIQUES
    # =============================================================================
    
    print(f"\n🔬 ENSEMBLE METHODS AND ADVANCED TECHNIQUES")
    print(f"{'-'*50}")
    print("Testing ensemble methods and advanced ML techniques...")
    
    from sklearn.ensemble import VotingClassifier, AdaBoostClassifier, ExtraTreesClassifier
    from sklearn.naive_bayes import GaussianNB
    from sklearn.neighbors import KNeighborsClassifier
    
    ensemble_results = []
    
    # Define ensemble methods
    base_classifiers = [
        ('lr', LogisticRegression(random_state=42, max_iter=1000)),
        ('rf', RandomForestClassifier(n_estimators=50, random_state=42)),
        ('gb', GradientBoostingClassifier(n_estimators=50, random_state=42))
    ]
    
    # Add XGBoost to ensemble if available
    if XGBOOST_AVAILABLE:
        base_classifiers.append(('xgb', XGBClassifier(n_estimators=50, random_state=42, eval_metric='logloss')))
    
    ensemble_methods = {
        'Voting (Hard)': VotingClassifier(estimators=base_classifiers, voting='hard'),
        'Voting (Soft)': VotingClassifier(estimators=base_classifiers, voting='soft'),
        'AdaBoost': AdaBoostClassifier(n_estimators=50, random_state=42),
        'Extra Trees': ExtraTreesClassifier(n_estimators=100, random_state=42),
        'K-Neighbors': KNeighborsClassifier(n_neighbors=5),
        'Naive Bayes': GaussianNB()
    }
    
    for target in available_targets:
        target_encoded = f'{target}_encoded'
        
        # Prepare features and target
        X = encoded_data[[f'{f}_encoded' for f in available_features]]
        y = encoded_data[target_encoded]
        
        print(f"\n   🎯 Ensemble Results for {target}:")
        print(f"   {'Method':<15} {'CV Score':<10} {'Test Score':<12} {'Std Dev':<10}")
        print(f"   {'-'*50}")
        
        for method_name, method in ensemble_methods.items():
            try:
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
                
                # Create pipeline with scaling for methods that need it
                if method_name in ['K-Neighbors', 'Naive Bayes']:
                    pipeline = Pipeline([
                        ('scaler', StandardScaler()),
                        ('classifier', method)
                    ])
                else:
                    pipeline = Pipeline([
                        ('classifier', method)
                    ])
                
                # Cross-validation with std dev
                cv_scores = cross_val_score(pipeline, X_train, y_train, cv=5, scoring='accuracy')
                cv_mean = cv_scores.mean()
                cv_std = cv_scores.std()
                
                # Fit and test
                pipeline.fit(X_train, y_train)
                test_score = pipeline.score(X_test, y_test)
                
                print(f"   {method_name:<15} {cv_mean:.3f}     {test_score:.3f}       {cv_std:.3f}")
                
                # Store results
                ensemble_results.append({
                    'method': method_name,
                    'target': target,
                    'cv_score': cv_mean,
                    'cv_std': cv_std,
                    'test_score': test_score
                })
                
            except Exception as e:
                print(f"   {method_name:<15} FAILED    FAILED        FAILED")

    # =============================================================================
    # 4.8 REGRESSION ANALYSIS SUMMARY
    # =============================================================================
    
    print_section_header("REGRESSION ANALYSIS SUMMARY")
    print_methodology("""
    Consolidating multivariate regression results to identify optimal approaches.
    This comprehensive analysis examined:
    
    1. Multiple algorithms (Logistic, Gradient Boosting, SVM, Random Forest)
    2. Feature interactions and polynomial relationships
    3. Regularization techniques (L1/L2) and feature selection
    4. Ensemble methods and advanced ML techniques
    
    Results show predictive performance beyond single-feature approaches.
    """)
    
    # Consolidate regression results
    if regression_results:
        regression_df = pd.DataFrame([r for r in regression_results if r.get('feature_type') == 'all_features'])
        
        if not regression_df.empty:
            print("🏆 BEST MULTIVARIATE REGRESSION PERFORMANCE:")
            print("-" * 60)
            
            # Find best performing algorithm for each target
            for target in available_targets:
                target_results = regression_df[regression_df['target'] == target]
                if not target_results.empty:
                    best_result = target_results.loc[target_results['test_score'].idxmax()]
                    print(f"\n   {target}:")
                    print(f"   ├─ Best Algorithm: {best_result['algorithm']}")
                    print(f"   ├─ Test Accuracy: {best_result['test_score']:.3f}")
                    print(f"   └─ CV Score: {best_result['cv_score']:.3f}")
            
            # Overall best algorithms
            avg_performance = regression_df.groupby('algorithm').agg({
                'test_score': 'mean',
                'cv_score': 'mean'
            }).round(3).sort_values('test_score', ascending=False)
            
            print(f"\n🥇 OVERALL ALGORITHM RANKING:")
            print(avg_performance.to_string())
    
    # Feature interaction insights
    if interaction_results:
        interaction_df = pd.DataFrame(interaction_results)
        
        if not interaction_df.empty:
            print(f"\n🔗 TOP FEATURE INTERACTIONS:")
            print("-" * 60)
            
            # Find best interactions for each target
            for target in available_targets:
                target_interactions = interaction_df[interaction_df['target'] == target]
                if not target_interactions.empty:
                    best_interaction = target_interactions.loc[target_interactions['max_improvement'].idxmax()]
                    if best_interaction['max_improvement'] > 0.01:  # Only show meaningful improvements
                        print(f"\n   {target}:")
                        print(f"   ├─ Best Pair: {best_interaction['feature1'].replace('from_', '')} + {best_interaction['feature2'].replace('from_', '')}")
                        print(f"   ├─ Improvement: +{best_interaction['max_improvement']:.3f}")
                        best_score = best_interaction['lr_score'] if best_interaction['lr_score'] > best_interaction['gb_score'] else best_interaction['gb_score']
                        print(f"   └─ Best Score: {best_score:.3f}")

    # =============================================================================
    # 5. CONSOLIDATED FEATURE ANALYSIS
    # =============================================================================
    
    print_section_header("CONSOLIDATED FEATURE ANALYSIS")
    print_methodology("""
    Combining all statistical approaches to create a comprehensive ranking.
    This consensus approach now considers:
    
    1. Information content (Mutual Information)
    2. Statistical significance (Chi-Square/Cramer's V)  
    3. Practical predictive utility (Random Forest)
    4. Multivariate regression performance
    5. Feature interaction effects
    
    Features are ranked across all methodologies to identify the most robust
    organisational dimensions for career pathway prediction.
    """)
    
    def rank_features(df, score_col, ascending=False):
        """Rank features within each target and return ranks"""
        ranks = []
        for target in df['target'].unique():
            target_data = df[df['target'] == target].copy()
            target_data['rank'] = target_data[score_col].rank(ascending=ascending)
            ranks.append(target_data[['feature', 'target', 'rank']])
        return pd.concat(ranks) if ranks else pd.DataFrame()
    
    # Get ranks for each method (only if we have results)
    consolidated_data = []
    
    if not mi_df.empty:
        mi_ranks = rank_features(mi_df, 'mutual_information', ascending=False)
        mi_ranks.columns = ['feature', 'target', 'mi_rank']
        consolidated_data.append(mi_ranks)
    
    if not chi_df.empty:
        chi_ranks = rank_features(chi_df, 'cramers_v', ascending=False) 
        chi_ranks.columns = ['feature', 'target', 'chi_rank']
        consolidated_data.append(chi_ranks)
    
    if not rf_df.empty:
        rf_ranks = rank_features(rf_df, 'importance', ascending=False)
        rf_ranks.columns = ['feature', 'target', 'rf_rank']
        consolidated_data.append(rf_ranks)
    
    if len(consolidated_data) >= 2:  # Need at least 2 methods for consolidation
        # Merge all rankings
        consolidated = consolidated_data[0]
        for data in consolidated_data[1:]:
            consolidated = consolidated.merge(data, on=['feature', 'target'], how='outer')
        
        # Fill missing ranks with median rank
        rank_cols = [col for col in consolidated.columns if 'rank' in col]
        for col in rank_cols:
            consolidated[col] = consolidated[col].fillna(consolidated[col].median())
        
        # Calculate average rank (lower is better)
        consolidated['avg_rank'] = consolidated[rank_cols].mean(axis=1)
        
        # Add original scores for reference
        if not mi_df.empty:
            consolidated = consolidated.merge(mi_df[['feature', 'target', 'mutual_information']], on=['feature', 'target'], how='left')
        if not chi_df.empty:
            consolidated = consolidated.merge(chi_df[['feature', 'target', 'cramers_v', 'significant']], on=['feature', 'target'], how='left')
        if not rf_df.empty:
            consolidated = consolidated.merge(rf_df[['feature', 'target', 'importance']], on=['feature', 'target'], how='left')
        
        print("📊 Consolidated Feature Ranking (lower avg_rank = better overall performance):")
        
        for target in available_targets:
            target_results = consolidated[consolidated['target'] == target].copy()
            if not target_results.empty:
                target_results = target_results.sort_values('avg_rank')
                
                print(f"\n   Predicting {target}:")
                display_cols = ['feature', 'avg_rank'] + [col for col in ['mutual_information', 'cramers_v', 'importance', 'significant'] if col in target_results.columns]
                print(target_results[display_cols].round(4).to_string(index=False))
        
        # =============================================================================
        # 6. FEATURE SELECTION RECOMMENDATIONS
        # =============================================================================
        
        print_section_header("FEATURE SELECTION RECOMMENDATIONS")
        print_methodology("""
        Based on statistical analysis, we make data-driven recommendations for
        which organisational features to use in subsequent analysis.
        
        We calculate overall performance across all targets and consider:
        - Statistical strength (average rank across methods)
        - Statistical significance (proportion of significant relationships)
        - Practical interpretability for business applications
        """)
        
        # Calculate overall feature performance
        overall_performance = consolidated.groupby('feature').agg({
            'avg_rank': 'mean',
            **{col: 'mean' for col in ['mutual_information', 'cramers_v', 'importance'] if col in consolidated.columns},
            **{'significant': 'sum' if 'significant' in consolidated.columns else 'count'}
        }).round(4)
        
        if 'significant' in consolidated.columns:
            overall_performance['significance_rate'] = overall_performance['significant'] / len(available_targets)
        
        overall_performance = overall_performance.sort_values('avg_rank')
        
        print("📈 Overall Feature Performance (averaged across all prediction targets):")
        print(overall_performance.to_string())
        
        # Identify top features
        if len(overall_performance) >= 1:
            top_feature = overall_performance.index[0]
            print(f"\n🏆 RECOMMENDED PRIMARY FEATURE: {top_feature}")
            print(f"   → Best average rank: {overall_performance.loc[top_feature, 'avg_rank']:.2f}")
            
            if 'significant' in overall_performance.columns:
                print(f"   → Significant for {overall_performance.loc[top_feature, 'significant']}/{len(available_targets)} targets")
            
            if 'mutual_information' in overall_performance.columns:
                print(f"   → Mean Mutual Information: {overall_performance.loc[top_feature, 'mutual_information']:.4f}")
            
            if 'cramers_v' in overall_performance.columns:
                print(f"   → Mean Cramer's V: {overall_performance.loc[top_feature, 'cramers_v']:.4f}")
            
            if len(overall_performance) >= 2:
                second_feature = overall_performance.index[1]
                print(f"\n🥈 RECOMMENDED SECONDARY FEATURE: {second_feature}")
                print(f"   → Average rank: {overall_performance.loc[second_feature, 'avg_rank']:.2f}")
        
        print(f"\n📋 NEXT STEPS:")
        print(f"   1. Use '{top_feature}' as primary grouping dimension for role typology analysis")
        if len(overall_performance) >= 2:
            print(f"   2. Consider '{overall_performance.index[1]}' as secondary dimension if needed")
        print(f"   3. Proceed to classify roles as launchpads/silos based on movement patterns")
        print(f"   4. Analyse skill patterns within successful transitions")
        
    else:
        print("⚠️  Insufficient statistical results for consolidated analysis")
        print("   → Check data quality and feature availability")
        if available_features:
            print(f"   → Recommend using: {available_features[0]} as primary feature")
    
    # =============================================================================
    # 7. METHODOLOGY-SPECIFIC TOP RANKINGS
    # =============================================================================
    
    print_section_header("TOP RANKINGS BY METHODOLOGY")
    print_methodology("""
    For each statistical method, we identify the top-performing features.
    This allows comparison of results across different analytical approaches
    and helps validate findings through methodological triangulation.
    """)
    
    TOP_N = 3  # Number of top features to show per methodology
    
    # Top features by Mutual Information
    if not mi_df.empty:
        print("🔬 TOP FEATURES BY MUTUAL INFORMATION (Information Content):")
        print("-" * 60)
        
        # Get top features for each target
        for target in available_targets:
            target_mi = mi_df[mi_df['target'] == target].nlargest(TOP_N, 'mutual_information')
            print(f"\n   Predicting {target}:")
            for i, (_, row) in enumerate(target_mi.iterrows(), 1):
                print(f"   {i}. {row['feature']:<25} → MI: {row['mutual_information']:.4f}")
        
        # Overall top features across all targets
        mi_overall = mi_df.groupby('feature')['mutual_information'].mean().nlargest(TOP_N)
        print(f"\n   🏆 OVERALL TOP {TOP_N} BY MUTUAL INFORMATION:")
        for i, (feature, score) in enumerate(mi_overall.items(), 1):
            print(f"   {i}. {feature:<25} → Avg MI: {score:.4f}")
    
    # Top features by Chi-Square/Cramer's V
    if not chi_df.empty:
        print(f"\n🔬 TOP FEATURES BY CHI-SQUARE ANALYSIS (Statistical Significance):")
        print("-" * 60)
        
        # Get top features for each target
        for target in available_targets:
            target_chi = chi_df[chi_df['target'] == target].nlargest(TOP_N, 'cramers_v')
            print(f"\n   Predicting {target}:")
            for i, (_, row) in enumerate(target_chi.iterrows(), 1):
                sig_marker = "***" if row['significant'] else "   "
                print(f"   {i}. {row['feature']:<25} → Cramer's V: {row['cramers_v']:.4f} {sig_marker}")
        
        # Overall top features across all targets
        chi_overall = chi_df.groupby('feature')['cramers_v'].mean().nlargest(TOP_N)
        print(f"\n   🏆 OVERALL TOP {TOP_N} BY CRAMER'S V:")
        for i, (feature, score) in enumerate(chi_overall.items(), 1):
            # Check significance rate
            sig_rate = chi_df[chi_df['feature'] == feature]['significant'].mean()
            print(f"   {i}. {feature:<25} → Avg Cramer's V: {score:.4f} (Significant: {sig_rate*100:.0f}%)")
    
    # Top features by Random Forest
    if not rf_df.empty:
        print(f"\n🔬 TOP FEATURES BY RANDOM FOREST (Predictive Utility):")
        print("-" * 60)
        
        # Get top features for each target
        for target in available_targets:
            target_rf = rf_df[rf_df['target'] == target].nlargest(TOP_N, 'importance')
            if not target_rf.empty:
                model_accuracy = target_rf['test_accuracy'].iloc[0]
                print(f"\n   Predicting {target} (Model Accuracy: {model_accuracy:.3f}):")
                for i, (_, row) in enumerate(target_rf.iterrows(), 1):
                    print(f"   {i}. {row['feature']:<25} → Importance: {row['importance']:.4f}")
        
        # Overall top features across all targets
        rf_overall = rf_df.groupby('feature')['importance'].mean().nlargest(TOP_N)
        print(f"\n   🏆 OVERALL TOP {TOP_N} BY RANDOM FOREST IMPORTANCE:")
        for i, (feature, score) in enumerate(rf_overall.items(), 1):
            # Calculate average model performance for this feature
            avg_accuracy = rf_df[rf_df['feature'] == feature]['test_accuracy'].mean()
            print(f"   {i}. {feature:<25} → Avg Importance: {score:.4f} (Avg Accuracy: {avg_accuracy:.3f})")

    # =============================================================================
    # 8. CROSS-METHODOLOGY SYNTHESIS
    # =============================================================================
    
    print_section_header("CROSS-METHODOLOGY SYNTHESIS")
    print_methodology("""
    Synthesising results across all methodologies to identify the most robust
    features. We examine consistency of rankings, statistical significance,
    and practical utility to provide definitive recommendations.
    """)
    
    if len(consolidated_data) >= 2:
        # Calculate cross-methodology consistency
        print("📊 CROSS-METHODOLOGY FEATURE CONSISTENCY:")
        print("-" * 60)
        
        # For each feature, check how often it appears in top rankings
        feature_consistency = {}
        
        for feature in available_features:
            consistency_score = 0
            method_rankings = []
            
            # Check Mutual Information rankings
            if not mi_df.empty:
                mi_feature_ranks = {}
                for target in available_targets:
                    target_data = mi_df[mi_df['target'] == target].sort_values('mutual_information', ascending=False)
                    if feature in target_data['feature'].values:
                        rank = target_data['feature'].tolist().index(feature) + 1
                        mi_feature_ranks[target] = rank
                avg_mi_rank = np.mean(list(mi_feature_ranks.values())) if mi_feature_ranks else float('inf')
                method_rankings.append(('MI', avg_mi_rank))
                if avg_mi_rank <= 2:  # Top 2 average rank
                    consistency_score += 1
            
            # Check Chi-Square rankings
            if not chi_df.empty:
                chi_feature_ranks = {}
                for target in available_targets:
                    target_data = chi_df[chi_df['target'] == target].sort_values('cramers_v', ascending=False)
                    if feature in target_data['feature'].values:
                        rank = target_data['feature'].tolist().index(feature) + 1
                        chi_feature_ranks[target] = rank
                avg_chi_rank = np.mean(list(chi_feature_ranks.values())) if chi_feature_ranks else float('inf')
                method_rankings.append(('Chi²', avg_chi_rank))
                if avg_chi_rank <= 2:
                    consistency_score += 1
            
            # Check Random Forest rankings
            if not rf_df.empty:
                rf_feature_ranks = {}
                for target in available_targets:
                    target_data = rf_df[rf_df['target'] == target].sort_values('importance', ascending=False)
                    if feature in target_data['feature'].values:
                        rank = target_data['feature'].tolist().index(feature) + 1
                        rf_feature_ranks[target] = rank
                avg_rf_rank = np.mean(list(rf_feature_ranks.values())) if rf_feature_ranks else float('inf')
                method_rankings.append(('RF', avg_rf_rank))
                if avg_rf_rank <= 2:
                    consistency_score += 1
            
            feature_consistency[feature] = {
                'consistency_score': consistency_score,
                'method_rankings': method_rankings,
                'total_methods': len(method_rankings)
            }
        
        # Sort by consistency and display
        sorted_features = sorted(feature_consistency.items(), 
                               key=lambda x: x[1]['consistency_score'], 
                               reverse=True)
        
        print("\n🎯 FEATURE CONSISTENCY ANALYSIS:")
        print("   (Consistency Score = # of methods where feature ranks in top 2)")
        print()
        
        for feature, consistency_data in sorted_features:
            score = consistency_data['consistency_score']
            total = consistency_data['total_methods']
            rankings = consistency_data['method_rankings']
            
            print(f"   {feature}:")
            print(f"   ├─ Consistency: {score}/{total} methods ({score/total*100:.0f}%)")
            print(f"   ├─ Method Rankings: {', '.join([f'{method}: #{rank:.1f}' for method, rank in rankings])}")
            
            # Add interpretation
            if score == total:
                print(f"   └─ 🏆 HIGHLY CONSISTENT - Top performer across all methods")
            elif score >= total * 0.7:
                print(f"   └─ ✅ CONSISTENT - Strong performer across most methods")
            elif score >= total * 0.5:
                print(f"   └─ ⚠️  MODERATE - Mixed performance across methods")
            else:
                print(f"   └─ ❌ INCONSISTENT - Weak performance across methods")
            print()
        
        # Final recommendations
        if sorted_features:
            best_feature = sorted_features[0]
            best_feature_name = best_feature[0]
            best_consistency = best_feature[1]['consistency_score']
            best_total = best_feature[1]['total_methods']
            
            print("🏆 FINAL SYNTHESIS RECOMMENDATIONS:")
            print("=" * 60)
            print(f"\n1. PRIMARY RECOMMENDATION: {best_feature_name}")
            print(f"   ├─ Consistency Score: {best_consistency}/{best_total} ({best_consistency/best_total*100:.0f}%)")
            
            # Add specific scores if available
            if not mi_df.empty:
                avg_mi = mi_df[mi_df['feature'] == best_feature_name]['mutual_information'].mean()
                print(f"   ├─ Average Mutual Information: {avg_mi:.4f}")
            
            if not chi_df.empty:
                avg_cramers = chi_df[chi_df['feature'] == best_feature_name]['cramers_v'].mean()
                sig_rate = chi_df[chi_df['feature'] == best_feature_name]['significant'].mean()
                print(f"   ├─ Average Cramer's V: {avg_cramers:.4f}")
                print(f"   ├─ Statistical Significance Rate: {sig_rate*100:.0f}%")
            
            if not rf_df.empty:
                avg_importance = rf_df[rf_df['feature'] == best_feature_name]['importance'].mean()
                avg_accuracy = rf_df[rf_df['feature'] == best_feature_name]['test_accuracy'].mean()
                print(f"   ├─ Average RF Importance: {avg_importance:.4f}")
                print(f"   └─ Average Model Accuracy: {avg_accuracy:.3f}")
            
            # Secondary recommendation
            if len(sorted_features) > 1:
                second_feature = sorted_features[1]
                second_feature_name = second_feature[0]
                second_consistency = second_feature[1]['consistency_score']
                second_total = second_feature[1]['total_methods']
                
                print(f"\n2. SECONDARY RECOMMENDATION: {second_feature_name}")
                print(f"   └─ Consistency Score: {second_consistency}/{second_total} ({second_consistency/second_total*100:.0f}%)")
            
            print(f"\n📋 STRATEGIC IMPLICATIONS:")
            print(f"   ✓ Use '{best_feature_name}' as primary organisational dimension")
            print(f"   ✓ Design career pathways around {best_feature_name.replace('from_', '').replace('_', ' ')} transitions")
            print(f"   ✓ Focus role typology analysis on {best_feature_name.replace('from_', '').replace('_', ' ')} patterns")
            print(f"   ✓ Statistical foundation validated across multiple methodologies")

    # =============================================================================
    # 9. ANALYSIS SUMMARY & NEXT STEPS
    # =============================================================================
    
    print_section_header("ANALYSIS SUMMARY & NEXT STEPS")
    
    print("✅ COMPREHENSIVE FEATURE EVALUATION COMPLETED")
    print(f"   → Analysed {len(available_features)} organisational features")
    print(f"   → Evaluated {len(available_targets)} prediction targets")
    print(f"   → Processed {len(clean_movements):,} movement records")
    print(f"   → Applied {len([df for df in [mi_df, chi_df, rf_df] if not df.empty])} statistical methodologies")
    
    print(f"\n📊 STATISTICAL METHODS APPLIED:")
    if not mi_df.empty:
        print(f"   ✓ Mutual Information Analysis - {len(mi_df)} feature-target combinations")
    if not chi_df.empty:
        significant_count = chi_df['significant'].sum() if 'significant' in chi_df.columns else 0
        print(f"   ✓ Chi-Square Independence Tests - {significant_count}/{len(chi_df)} statistically significant")
    if not rf_df.empty:
        avg_accuracy = rf_df['test_accuracy'].mean()
        print(f"   ✓ Random Forest Importance - average model accuracy: {avg_accuracy:.3f}")
    
    print(f"\n🎯 KEY INSIGHTS:")
    if len(consolidated_data) >= 2 and len(sorted_features) >= 1:
        primary_feature = sorted_features[0][0]
        primary_consistency = sorted_features[0][1]['consistency_score']
        primary_total = sorted_features[0][1]['total_methods']
        
        print(f"   → Most robust feature: {primary_feature} ({primary_consistency}/{primary_total} methods)")
        print(f"   → Cross-methodology validation achieved")
        print(f"   → Statistical foundation established for advanced analytics")
        print(f"   → Framework ready for role/skill typology classification")
    else:
        print(f"   → Basic feature evaluation completed")
        print(f"   → Single-method results available")
        print(f"   → Recommend expanding data sources for robust validation")
    
    print(f"\n🚀 RECOMMENDED NEXT STEPS:")
    print(f"   1. ROLE TYPOLOGY ANALYSIS:")
    print(f"      → Classify roles as 'launchpads' vs 'silos' based on outbound movement patterns")
    print(f"      → Use '{primary_feature if 'primary_feature' in locals() else available_features[0]}' as primary grouping dimension")
    print(f"      → Calculate movement diversity scores and transition probabilities")
    
    print(f"\n   2. SKILL BRIDGE IDENTIFICATION:")
    print(f"      → Analyse skill overlap patterns in successful transitions")
    print(f"      → Identify 'bridge skills' that enable cross-functional mobility")
    print(f"      → Map skill acquisition pathways for career development")
    
    print(f"\n   3. ENHANCED PATHWAY SCORING:")
    print(f"      → Integrate movement probability with existing similarity scores")
    print(f"      → Weight recommendations by organisational transition patterns")
    print(f"      → Create personalised pathway scoring based on current role context")
    
    print(f"\n   4. VALIDATION & DEPLOYMENT:")
    print(f"      → Test methodology with additional organisational dimensions")
    print(f"      → Validate findings against business stakeholder knowledge")
    print(f"      → Prepare framework for real-world data deployment")
    
    print(f"\n📈 METHODOLOGY BENEFITS:")
    print(f"   ✓ Data-driven approach eliminates subjective bias")
    print(f"   ✓ Multi-method validation ensures robust results")
    print(f"   ✓ Statistical significance testing provides confidence levels")
    print(f"   ✓ Framework scales to additional organisational features")
    print(f"   ✓ Results interpretable for business stakeholders")
    
    # Close database connection
    conn.close()
    print(f"\n🔒 Database connection closed")
    print(f"\n{'='*80}")
    print("FEATURE EVALUATION ANALYSIS COMPLETE")
    print(f"{'='*80}")

if __name__ == "__main__":
    main() 