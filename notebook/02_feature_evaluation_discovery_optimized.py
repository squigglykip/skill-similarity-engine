#!/usr/bin/env python3
"""
Feature Evaluation & Movement Data Discovery - Enhanced Version

This enhanced version includes:
1. Expanded feature set based on business logic and data quality analysis
2. Comprehensive univariate analysis (single feature predictors)
3. True multivariate analysis (multiple features combined)
4. Memory-efficient processing for large datasets
5. Detailed insights into what predicts career moves

The analysis now covers movement characteristics, job architecture, 
organisational context, and employment patterns.
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
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import Ridge, Lasso, ElasticNet
from sklearn.feature_selection import SelectKBest, f_classif, RFE
from sklearn.ensemble import VotingClassifier, AdaBoostClassifier, ExtraTreesClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.feature_selection import SelectFromModel
from sklearn.ensemble import IsolationForest
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import warnings
import gc
import psutil
import os
from pathlib import Path
from datetime import datetime, timedelta
warnings.filterwarnings('ignore')

# Import XGBoost with fallback
try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

# Import progress tracking utilities
try:
    from src.skill_similarity_engine.utils.progress import ProgressTracker, SimpleProgressReporter
    PROGRESS_AVAILABLE = True
except ImportError:
    PROGRESS_AVAILABLE = False
    print("   ⚠️  Progress tracking not available")

# Set plotting style
plt.style.use('default')
sns.set_palette("husl")

# =============================================================================
# CONFIGURATION - SET YOUR FILE PATHS HERE
# =============================================================================

# DATABASE FILE PATH - UPDATE THIS TO YOUR ACTUAL DATABASE LOCATION  
DATABASE_FILE = "models/2025-Q3/workforce_intelligence.sqlite"

# =============================================================================
# ENHANCED FEATURE CONFIGURATION
# =============================================================================

# Expanded feature set based on business logic and data quality analysis
ENHANCED_FEATURES = {
    # Movement characteristics (definitive patterns)
    'movement_features': [
        'movement_count',
        'avg_days_between'
    ],
    
    # Job architecture (core predictors)
    'job_architecture_features': [
        'from_job_function',
        'from_job_sub_function', 
        'from_job_category',
        'from_management_level'
    ],
    
    # Organisational context (movement patterns)
    'organisational_features': [
        'from_division',
        'from_business_unit',
        'from_salary_group'
    ],
    
    # Employment context (mobility patterns) - REMOVED: employee_group reflects personal choices, not career development
    'employment_features': [
        # 'from_employee_group'  # Excluded: 87% accuracy but represents personal life choices (FT/PT transitions)
    ]
}

# Target variables (same structure as features)
ENHANCED_TARGETS = {
    'job_architecture_targets': [
        'to_job_function',
        'to_job_sub_function',
        'to_job_category',
        'to_management_level'
    ],
    
    'organisational_targets': [
        'to_division',
        'to_business_unit',
        'to_salary_group'
    ],
    
    'employment_targets': [
        # 'to_employee_group'  # Excluded: represents personal life choices, not career progression
    ]
}

# =============================================================================
# MEMORY MANAGEMENT UTILITIES
# =============================================================================

def get_memory_usage():
    """Get current memory usage information"""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    return {
        'current_process_usage_mb': memory_info.rss / 1024 / 1024,
        'available_memory_mb': psutil.virtual_memory().available / 1024 / 1024
    }

def trigger_garbage_collection():
    """Trigger garbage collection to free memory"""
    gc.collect()

def chunk_dataframe(df, chunk_size=5000):
    """Yield successive chunks from dataframe"""
    for i in range(0, len(df), chunk_size):
        yield df.iloc[i:i + chunk_size]

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

def print_memory_status():
    """Print current memory usage"""
    memory_usage = get_memory_usage()
    print(f"💾 Memory: {memory_usage['current_process_usage_mb']:.1f} MB")

def normalize_column_names(df):
    """
    Normalize column names to lowercase with underscores for consistent access
    """
    # Create a mapping of original names to normalized names
    column_mapping = {}
    for col in df.columns:
        # Convert to lowercase and replace spaces with underscores
        normalized = col.lower().replace(' ', '_').replace('-', '_')
        column_mapping[col] = normalized
    
    # Rename columns
    df_normalized = df.rename(columns=column_mapping)
    
    # Print column mapping for transparency
    print(f"📋 Column name normalization:")
    for original, normalized in column_mapping.items():
        if original != normalized:
            print(f"   → '{original}' → '{normalized}'")
    
    return df_normalized

def load_movement_data_from_database(conn):
    """
    Load movement data from the movement_fact table in the database
    Automatically normalizes column names for consistent access
    """
    print(f"📁 Loading movement data from database table: movement_fact")
    
    try:
        # Load movement data from the movement_fact table
        query = """
        SELECT 
            from_position,
            to_position,
            movement_pattern,
            movement_count,
            movement_year,
            movement_month,
            avg_days_between,
            predominant_movement_type
        FROM movement_fact
        """
        
        df = pd.read_sql_query(query, conn)
        
        # Normalize column names for consistent access
        df = normalize_column_names(df)
        
        print(f"✅ Successfully loaded {len(df):,} records from movement_fact table")
        
        # Show data range for context
        if 'movement_year' in df.columns:
            min_year = df['movement_year'].min()
            max_year = df['movement_year'].max()
            print(f"📅 Data range: {min_year} - {max_year}")
        
        return df
        
    except Exception as e:
        raise RuntimeError(f"Failed to load movement data from database: {str(e)}")

def calculate_aggressive_recency_weight(movement_date, reference_date=None, decay_rate=0.4):
    """
    Aggressive decay for fast-changing banking environment
    decay_rate=0.4 means each year back loses 60% of relevance
    """
    if reference_date is None:
        reference_date = datetime.now()
    
    # Convert to pandas datetime for consistent handling
    movement_date = pd.to_datetime(movement_date)
    reference_date = pd.to_datetime(reference_date)
    
    # Calculate years difference
    days_diff = (reference_date - movement_date).days
    years_ago = days_diff / 365.25
    
    weight = decay_rate ** years_ago
    
    return max(weight, 0.05)  # Minimum weight threshold

def create_clean_movement_dataset(movement_df, job_arch_df):
    """
    Conservative null exclusion with steep recency weighting
    """
    original_count = len(movement_df)
    
    # Step 1: Only keep movements where both positions exist in current job arch
    print(f"   → Initial records: {len(movement_df):,}")
    
    # Check if JobProfileID columns exist
    required_cols = ['JobProfileID_from', 'JobProfileID_to']
    missing_cols = [col for col in required_cols if col not in movement_df.columns]
    if missing_cols:
        print(f"   ⚠️  Missing columns: {missing_cols}")
        print(f"   → Available columns: {list(movement_df.columns)}")
        # Skip job profile filtering if columns don't exist
        clean_df = movement_df.copy()
    else:
        clean_df = movement_df.dropna(subset=['JobProfileID_from', 'JobProfileID_to'])
        print(f"   → After dropping null JobProfileIDs: {len(clean_df):,}")
        
        current_job_profiles = set(job_arch_df['JobProfileID'].unique())
        print(f"   → Current job profiles available: {len(current_job_profiles):,}")
        
        before_filter = len(clean_df)
        clean_df = clean_df[
            clean_df['JobProfileID_from'].isin(current_job_profiles) &
            clean_df['JobProfileID_to'].isin(current_job_profiles)
        ]
        print(f"   → After job profile filtering: {len(clean_df):,} (removed {before_filter - len(clean_df):,})")
    
    # Step 2: Apply aggressive recency weighting
    # Convert movement_date if needed
    if 'movement_date' in clean_df.columns:
        # Ensure movement_date is datetime
        clean_df = clean_df.copy()
        clean_df['movement_date'] = pd.to_datetime(clean_df['movement_date'])
        clean_df['recency_weight'] = clean_df['movement_date'].apply(
            calculate_aggressive_recency_weight
        )
    elif 'movement_year' in clean_df.columns:
        # Create date from year and calculate weights
        clean_df = clean_df.copy()
        clean_df['movement_date'] = pd.to_datetime(clean_df['movement_year'], format='%Y')
        # Calculate recency weights as float values
        recency_weights = []
        for date_val in clean_df['movement_date']:
            weight = calculate_aggressive_recency_weight(date_val)
            recency_weights.append(weight)
        clean_df['recency_weight'] = recency_weights
    else:
        print("⚠️  No date column found, using uniform weights")
        clean_df = clean_df.copy()
        clean_df['recency_weight'] = 1.0
    
    # Step 3: Filter out movements with negligible weight
    # Ensure recency_weight is numeric before comparison
    clean_df['recency_weight'] = pd.to_numeric(clean_df['recency_weight'], errors='coerce')
    clean_df = clean_df[clean_df['recency_weight'] >= 0.01]
    
    # Simple retention reporting by year
    if 'movement_year' in movement_df.columns:
        print("Data retention by year:")
        for year in sorted(movement_df['movement_year'].unique()):
            original_year = len(movement_df[movement_df['movement_year'] == year])
            clean_year = len(clean_df[clean_df['movement_year'] == year])
            retention = (clean_year / original_year * 100) if original_year > 0 else 0
            print(f"  {year}: {retention:.1f}%")
    
    total_retention = len(clean_df) / original_count * 100
    print(f"Overall retention: {total_retention:.1f}%")
    
    return clean_df

def enrich_movement_data_with_context(movement_df, jobs_df, positions_df, workforce_context_df):
    """
    Enhanced data enrichment with organisational and employment context
    """
    print("🔄 Enhanced data enrichment with expanded context...")
    
    # Check available columns in positions_df
    print(f"   → Available columns in positions: {list(positions_df.columns)}")
    
    # Create clean position mapping with available columns
    base_columns = ['Position Number', 'JobProfileID']
    optional_columns = {
        'Division': 'Division',
        'Business_Unit': 'Business_Unit', 
        'Salary_Group': ['Salary_Group', 'Salary Group'],  # Try underscore first (schema shows this)
        'Employee_Group': ['Employee_Group', 'Employee Group']  # Try underscore first (schema shows this)
    }
    
    # Find available columns
    available_columns = base_columns.copy()
    column_mapping = {}
    
    for target_col, source_variants in optional_columns.items():
        if isinstance(source_variants, str):
            source_variants = [source_variants]
        
        for variant in source_variants:
            if variant in positions_df.columns:
                available_columns.append(variant)
                column_mapping[variant] = target_col
                print(f"   → Found {variant} → will map to {target_col}")
                break
        else:
            print(f"   ⚠️  {target_col} not found in positions (tried: {source_variants})")
    
    # Create clean position mapping with available columns
    clean_positions = positions_df[available_columns].drop_duplicates('Position Number')
    
    # Rename columns to standard format
    clean_positions = clean_positions.rename(columns=column_mapping)
    
    print(f"   → Position mapping columns: {list(clean_positions.columns)}")
    
    # Also get workforce context for employee_group if available
    if not workforce_context_df.empty:
        print(f"   → Workforce context columns: {list(workforce_context_df.columns)}")
        if 'employee_group' in workforce_context_df.columns:
            try:
                workforce_mapping = workforce_context_df[['position_number', 'employee_group']].drop_duplicates('position_number')
                workforce_mapping = workforce_mapping.rename(columns={'position_number': 'Position Number'})
                
                # Merge workforce context with positions
                before_merge_cols = set(clean_positions.columns)
                clean_positions = clean_positions.merge(
                    workforce_mapping, 
                    on='Position Number', 
                    how='left',
                    suffixes=('', '_workforce')
                )
                after_merge_cols = set(clean_positions.columns)
                
                # Check what columns were actually created by the merge
                new_cols = after_merge_cols - before_merge_cols
                print(f"   → New columns after workforce merge: {new_cols}")
                
                # Handle the employee_group column properly
                if 'employee_group_workforce' in clean_positions.columns:
                    if 'Employee_Group' in clean_positions.columns:
                        clean_positions['Employee_Group'] = clean_positions['employee_group_workforce'].fillna(clean_positions['Employee_Group'])
                    else:
                        clean_positions['Employee_Group'] = clean_positions['employee_group_workforce']
                    clean_positions = clean_positions.drop(['employee_group_workforce'], axis=1)
                    print(f"   → Enhanced Employee_Group with workforce context")
                else:
                    print(f"   ⚠️  Workforce merge didn't create expected employee_group_workforce column")
            except Exception as e:
                print(f"   ⚠️  Workforce context merge failed: {str(e)}")
                print(f"   → Continuing with positions data only")
    
    print(f"   → Enhanced position mapping: {len(clean_positions):,} positions with full context")
    
    # Process in chunks if dataset is large
    if len(movement_df) > 100000:
        print(f"   → Processing {len(movement_df):,} records in chunks...")
        
        enriched_chunks = []
        for chunk in chunk_dataframe(movement_df, chunk_size=10000):
            chunk_enriched = enrich_movement_chunk(chunk, clean_positions, jobs_df)
            enriched_chunks.append(chunk_enriched)
            trigger_garbage_collection()
        
        # Combine all chunks
        movements_df = pd.concat(enriched_chunks, ignore_index=True)
        del enriched_chunks
        
    else:
        movements_df = enrich_movement_chunk(movement_df, clean_positions, jobs_df)
    
    return movements_df
def enrich_movement_chunk(chunk, clean_positions, jobs_df):
    """
    Enrich a single chunk of movement data with full context
    """
    # Step 1: Merge with FROM positions (enhanced)
    chunk_enriched = chunk.merge(
        clean_positions,
        left_on='from_position',
        right_on='Position Number',
        how='left',
        suffixes=('', '_from')
    ).drop('Position Number', axis=1)
    
    # Rename FROM columns - only rename columns that exist
    rename_mapping_from = {'JobProfileID': 'JobProfileID_from'}
    
    # Add optional columns if they exist
    optional_from_renames = {
        'Division': 'from_division',
        'Business_Unit': 'from_business_unit',
        'Salary_Group': 'from_salary_group',
        'Employee_Group': 'from_employee_group'
    }
    
    for source_col, target_col in optional_from_renames.items():
        if source_col in chunk_enriched.columns:
            rename_mapping_from[source_col] = target_col
    
    chunk_enriched = chunk_enriched.rename(columns=rename_mapping_from)
    
    # Step 2: Merge with TO positions (enhanced)
    chunk_enriched = chunk_enriched.merge(
        clean_positions,
        left_on='to_position',
        right_on='Position Number',
        how='left',
        suffixes=('', '_to')
    ).drop('Position Number', axis=1)
    
    # Rename TO columns - only rename columns that exist
    rename_mapping_to = {'JobProfileID': 'JobProfileID_to'}
    
    # Add optional columns if they exist
    optional_to_renames = {
        'Division': 'to_division',
        'Business_Unit': 'to_business_unit',
        'Salary_Group': 'to_salary_group',
        'Employee_Group': 'to_employee_group'
    }
    
    for source_col, target_col in optional_to_renames.items():
        if source_col in chunk_enriched.columns:
            rename_mapping_to[source_col] = target_col
    
    chunk_enriched = chunk_enriched.rename(columns=rename_mapping_to)
    
    # Step 3: Merge with FROM jobs
    chunk_enriched = chunk_enriched.merge(
        jobs_df[['JobProfileID', 'JobFunction', 'JobSubFunction', 'ManagementLevel', 'JobCategory']],
        left_on='JobProfileID_from',
        right_on='JobProfileID',
        how='left',
        suffixes=('', '_from')
    ).drop('JobProfileID', axis=1)
    
    # Step 4: Merge with TO jobs
    chunk_enriched = chunk_enriched.merge(
        jobs_df[['JobProfileID', 'JobFunction', 'JobSubFunction', 'ManagementLevel', 'JobCategory']],
        left_on='JobProfileID_to',
        right_on='JobProfileID',
        how='left',
        suffixes=('_from', '_to')
    ).drop('JobProfileID', axis=1)
    
    # Rename job columns
    chunk_enriched = chunk_enriched.rename(columns={
        'JobFunction_from': 'from_job_function',
        'JobSubFunction_from': 'from_job_sub_function',
        'JobCategory_from': 'from_job_category',
        'ManagementLevel_from': 'from_management_level',
        'JobFunction_to': 'to_job_function',
        'JobSubFunction_to': 'to_job_sub_function',
        'JobCategory_to': 'to_job_category',
        'ManagementLevel_to': 'to_management_level'
    })
    
    return chunk_enriched

# =============================================================================
# ENHANCED STATISTICAL ANALYSIS FUNCTIONS
# =============================================================================

def safe_mutual_information(X, y, chunk_size=100000):
    """
    Calculate mutual information with full dataset processing using chunked approach
    """
    if len(X) <= chunk_size:
        return mutual_info_classif(X, y, random_state=42)
    
    print(f"   → Processing full dataset ({len(X):,} samples) in chunks for MI calculation")
    
    # Use a stratified approach to ensure we get representative chunks
    from sklearn.model_selection import StratifiedKFold
    
    # Use fewer folds for very large datasets to get bigger chunks
    n_folds = min(5, max(2, len(X) // chunk_size))
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=42)
    
    mi_scores_list = []
    
    for fold_idx, (_, chunk_indices) in enumerate(skf.split(X, y)):
        X_chunk = X.iloc[chunk_indices]
        y_chunk = y.iloc[chunk_indices]
        
        print(f"   → Processing MI chunk {fold_idx + 1}/{n_folds} ({len(X_chunk):,} samples)")
        
        chunk_mi = mutual_info_classif(X_chunk, y_chunk, random_state=42)
        mi_scores_list.append(chunk_mi)
        
        # Memory cleanup
        trigger_garbage_collection()
    
    # Combine results by averaging (weighted by chunk size if needed)
    combined_mi = np.mean(mi_scores_list, axis=0)
    
    print(f"   → Combined MI scores from {len(mi_scores_list)} chunks")
    return combined_mi

def safe_chi_square_test(X, y, chunk_size=100000):
    """
    Perform chi-square test with full dataset processing using chunked approach
    """
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
    
    results = []
    
    if len(X) <= chunk_size:
        # Process directly for smaller datasets
        for col in X.columns:
            try:
                contingency_table = pd.crosstab(X[col], y)
                chi2, p_value, dof, expected = chi2_contingency(contingency_table)
                cramers_v_score = cramers_v(X[col], y)
                
                results.append({
                    'feature': col,
                    'chi_square': chi2,
                    'p_value': p_value,
                    'degrees_of_freedom': dof,
                    'cramers_v': cramers_v_score,
                    'significant': bool(p_value < 0.05) if isinstance(p_value, (int, float)) else False
                })
            except Exception as e:
                print(f"   ⚠️  Chi-square test failed for {col}: {str(e)}")
    else:
        # Process in chunks and combine contingency tables
        print(f"   → Processing full dataset ({len(X):,} samples) in chunks for chi-square test")
        
        for col in X.columns:
            try:
                print(f"   → Processing feature {col} in chunks...")
                
                # Build combined contingency table from chunks
                combined_contingency = None
                
                for chunk_start in range(0, len(X), chunk_size):
                    chunk_end = min(chunk_start + chunk_size, len(X))
                    X_chunk = X.iloc[chunk_start:chunk_end]
                    y_chunk = y.iloc[chunk_start:chunk_end]
                    
                    # Get contingency table for this chunk
                    chunk_contingency = pd.crosstab(X_chunk[col], y_chunk)
                    
                    # Combine with overall contingency table
                    if combined_contingency is None:
                        combined_contingency = chunk_contingency
                    else:
                        # Add chunk contingency to combined, handling missing categories
                        combined_contingency = combined_contingency.add(chunk_contingency, fill_value=0)
                    
                    # Memory cleanup
                    trigger_garbage_collection()
                
                # Perform chi-square test on combined contingency table
                if combined_contingency is not None:
                    chi2, p_value, dof, expected = chi2_contingency(combined_contingency)
                    
                    # Calculate Cramer's V from combined table
                    n = combined_contingency.sum().sum()
                    phi2 = chi2 / n
                    r, k = combined_contingency.shape
                    phi2corr = max(0, phi2 - ((k-1)*(r-1))/(n-1))
                    rcorr = r - ((r-1)**2)/(n-1)
                    kcorr = k - ((k-1)**2)/(n-1)
                    cramers_v_score = np.sqrt(phi2corr / min(kcorr-1, rcorr-1))
                    
                    results.append({
                        'feature': col,
                        'chi_square': chi2,
                        'p_value': p_value,
                        'degrees_of_freedom': dof,
                        'cramers_v': cramers_v_score,
                        'significant': bool(p_value < 0.05) if isinstance(p_value, (int, float)) else False
                    })
                
            except Exception as e:
                print(f"   ⚠️  Chi-square test failed for {col}: {str(e)}")
    
    return results

def perform_univariate_analysis(encoded_data, available_features, available_targets):
    """
    Comprehensive univariate analysis - each feature predicting each target individually
    """
    print_section_header("COMPREHENSIVE UNIVARIATE ANALYSIS")
    print_methodology("""
    Univariate analysis tests each feature individually as a predictor:
    1. Single feature → single target predictions
    2. Mutual information scores for feature importance
    3. Chi-square tests for statistical significance
    4. Individual algorithm performance per feature
    5. Feature ranking by predictive power
    
    This helps identify which single factors are most predictive of career moves.
    """)
    
    univariate_results = []
    
    # Test each feature individually against each target
    for target in available_targets:
        target_encoded = f'{target}_encoded'
        y = encoded_data[target_encoded]
        
        print(f"\n🎯 UNIVARIATE ANALYSIS FOR: {target}")
        print(f"{'Feature':<35} {'MI Score':<12} {'Chi²':<12} {'Accuracy':<12} {'Status':<12}")
        print("-" * 85)
        
        for feature in available_features:
            feature_encoded = f'{feature}_encoded'
            
            try:
                # Single feature analysis
                X = encoded_data[[feature_encoded]]
                
                # Mutual Information
                mi_score = mutual_info_classif(X, y, random_state=42)[0]
                
                # Chi-square test
                chi_results = safe_chi_square_test(X, y)
                chi_square = chi_results[0]['chi_square'] if chi_results else 0.0
                
                # Simple Random Forest for accuracy
                rf = RandomForestClassifier(n_estimators=50, random_state=42)
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
                rf.fit(X_train, y_train)
                accuracy = rf.score(X_test, y_test)
                
                status = "✅ GOOD" if accuracy > 0.6 else "⚠️ WEAK" if accuracy > 0.4 else "❌ POOR"
                
                print(f"{feature:<35} {mi_score:.4f}      {chi_square:.2f}      {accuracy:.3f}      {status}")
                
                # Store results
                univariate_results.append({
                    'feature': feature,
                    'target': target,
                    'mutual_information': mi_score,
                    'chi_square': chi_square,
                    'accuracy': accuracy,
                    'feature_category': get_feature_category(feature),
                    'target_category': get_target_category(target)
                })
                
            except Exception as e:
                print(f"{feature:<35} ERROR     ERROR     ERROR     ❌ {str(e)[:20]}...")
                univariate_results.append({
                    'feature': feature,
                    'target': target,
                    'mutual_information': 0.0,
                    'chi_square': 0.0,
                    'accuracy': 0.0,
                    'feature_category': get_feature_category(feature),
                    'target_category': get_target_category(target)
                })
    
    return pd.DataFrame(univariate_results)

def perform_multivariate_analysis(encoded_data, available_features, available_targets):
    """
    True multivariate analysis - multiple features predicting targets
    """
    print_section_header("TRUE MULTIVARIATE ANALYSIS")
    print_methodology("""
    Multivariate analysis uses multiple features together:
    1. Feature combinations by category (job, org, employment)
    2. Full feature set predictions
    3. Feature selection techniques
    4. Algorithm comparison with multiple inputs
    5. Feature importance analysis
    
    This reveals how features interact and combine to predict career moves.
    """)
    
    multivariate_results = []
    
    # Define feature combinations
    feature_combinations = {
        'Movement Only': [f for f in available_features if f in ['movement_count', 'avg_days_between']],
        'Job Architecture': [f for f in available_features if 'job_' in f or 'management_' in f],
        'Organisational': [f for f in available_features if 'division' in f or 'business_unit' in f or 'salary_group' in f],
        # 'Employment': [f for f in available_features if 'employee_group' in f],  # Excluded: personal life choices
        'Job + Org': [f for f in available_features if 'job_' in f or 'management_' in f or 'division' in f or 'business_unit' in f or 'salary_group' in f],
        'All Features': available_features
    }
    
    # Algorithms optimized for multivariate analysis
    algorithms = {
        'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
        'Gradient Boosting': GradientBoostingClassifier(n_estimators=100, random_state=42),
        'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42),
        'Extra Trees': ExtraTreesClassifier(n_estimators=100, random_state=42)
    }
    
    # Add XGBoost if available
    if XGBOOST_AVAILABLE:
        algorithms['XGBoost'] = XGBClassifier(n_estimators=100, random_state=42, eval_metric='logloss')
    
    for target in available_targets:
        target_encoded = f'{target}_encoded'
        y = encoded_data[target_encoded]
        
        print(f"\n🎯 MULTIVARIATE ANALYSIS FOR: {target}")
        print(f"{'Feature Set':<20} {'Algorithm':<20} {'Accuracy':<12} {'Features':<10} {'Status':<12}")
        print("-" * 80)
        
        for combo_name, feature_list in feature_combinations.items():
            # Skip if no features in this combination
            if not feature_list:
                continue
                
            # Filter to available features
            available_combo_features = [f for f in feature_list if f in available_features]
            if not available_combo_features:
                continue
            
            # Prepare feature matrix
            X = encoded_data[[f'{f}_encoded' for f in available_combo_features]]
            
            for alg_name, algorithm in algorithms.items():
                try:
                    # Split data
                    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
                    
                    # Create pipeline with scaling if needed
                    if alg_name == 'Logistic Regression':
                        pipeline = Pipeline([
                            ('scaler', StandardScaler()),
                            ('classifier', algorithm)
                        ])
    else:
                        pipeline = Pipeline([
                            ('classifier', algorithm)
                        ])
                    
                    # Fit and evaluate
                    pipeline.fit(X_train, y_train)
                    accuracy = pipeline.score(X_test, y_test)
                    
                    status = "✅ GOOD" if accuracy > 0.6 else "⚠️ WEAK" if accuracy > 0.4 else "❌ POOR"
                    
                    print(f"{combo_name:<20} {alg_name:<20} {accuracy:.3f}      {len(available_combo_features):<10} {status}")
                    
                    # Store results
                    multivariate_results.append({
                        'feature_set': combo_name,
                        'algorithm': alg_name,
                        'target': target,
                        'accuracy': accuracy,
                        'num_features': len(available_combo_features),
                        'features': available_combo_features,
                        'target_category': get_target_category(target)
                    })
                    
                except Exception as e:
                    print(f"{combo_name:<20} {alg_name:<20} ERROR     {len(available_combo_features) if available_combo_features else 0:<10} ❌ {str(e)[:20]}...")
                    multivariate_results.append({
                        'feature_set': combo_name,
                        'algorithm': alg_name,
                        'target': target,
                        'accuracy': 0.0,
                        'num_features': len(available_combo_features) if available_combo_features else 0,
                        'features': available_combo_features,
                        'target_category': get_target_category(target)
                    })
    
    return pd.DataFrame(multivariate_results)

def get_feature_category(feature):
    """Categorize features by type"""
    if 'job_' in feature or 'management_' in feature:
        return 'Job Architecture'
    elif 'division' in feature or 'business_unit' in feature or 'salary_group' in feature:
        return 'Organisational'
    # elif 'employee_group' in feature:  # Excluded: personal life choices, not career development
    #     return 'Employment'
    elif feature in ['movement_count', 'avg_days_between']:
        return 'Movement'
    else:
        return 'Other'

def get_target_category(target):
    """Categorize targets by type"""
    if 'job_' in target or 'management_' in target:
        return 'Job Architecture'
    elif 'division' in target or 'business_unit' in target or 'salary_group' in target:
        return 'Organisational'
    # elif 'employee_group' in target:  # Excluded: personal life choices, not career development
    #     return 'Employment'
    else:
        return 'Other'

def memory_efficient_cross_validation(algorithm, X, y, cv=5, sample_weight=None):
    """
    Perform cross-validation with memory efficiency, proper stratification, and sample weights
    """
    from sklearn.model_selection import StratifiedKFold
    
    # Use stratified k-fold to maintain class distribution
    skf = StratifiedKFold(n_splits=cv, shuffle=True, random_state=42)
    scores = []
    
        for fold, (train_idx, val_idx) in enumerate(skf.split(X, y)):
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
            
        # Fit algorithm
            algorithm.fit(X_train, y_train)
            
            # Evaluate on validation set
            score = algorithm.score(X_val, y_val)
            scores.append(score)
            
            print(f"   Fold {fold + 1}/{cv}: {score:.3f}")
            
            # Memory cleanup between folds
            trigger_garbage_collection()
    
    return np.array(scores)

def safe_label_encoding(data, column_name, max_categories=1000):
    """
    Perform label encoding with memory efficiency and category limits
    """
    le = LabelEncoder()
    
    # Get unique values and check if we need to limit categories
    unique_values = data[column_name].astype(str).unique()
    
    if len(unique_values) > max_categories:
        print(f"   → Limiting {column_name} to top {max_categories} categories")
        # Keep top N most frequent categories
        value_counts = data[column_name].value_counts()
        top_categories = value_counts.head(max_categories).index.tolist()
        
        # Replace less frequent categories with 'OTHER'
        data_processed = data[column_name].where(
            data[column_name].isin(top_categories), 
            'OTHER'
        ).astype(str)
    else:
        data_processed = data[column_name].astype(str)
    
    # Fit encoder on full processed data
    encoded_values = le.fit_transform(data_processed)
    
    return encoded_values, le

# =============================================================================
# MAIN ANALYSIS FUNCTION
# =============================================================================

def main():
    """Enhanced main analysis function with univariate and multivariate analysis"""
    
    print_section_header(
        "ENHANCED FEATURE EVALUATION & PREDICTIVE MOVEMENT ANALYSIS",
        "Comprehensive univariate and multivariate analysis to understand career move predictors"
    )
    
    print("🚀 ENHANCED ANALYSIS FEATURES:")
    print("   → Expanded feature set (movement, job, org, employment)")
    print("   → Comprehensive univariate analysis (single predictors)")
    print("   → True multivariate analysis (feature combinations)")
    print("   → Memory-efficient processing for large datasets")
    print("   → Detailed insights into career move predictors")
    
    print_memory_status()
    
    # =============================================================================
    # 1. DATA LOADING AND INVESTIGATION
    # =============================================================================
    
    print_section_header("DATA LOADING AND INVESTIGATION")
    print_methodology("""
    Loading data with enhanced context:
    1. Load movement data from database
    2. Load job architecture, positions, and workforce context
    3. Enrich movements with full organisational context
    4. Prepare expanded feature set for analysis
    """)
    
    # Connect to database
    print(f"🔗 Connecting to database: {DATABASE_FILE}")
    
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        print(f"✅ Successfully connected to database: {DATABASE_FILE}")
    except sqlite3.OperationalError as e:
        raise FileNotFoundError(f"Could not connect to database: {DATABASE_FILE}. Error: {str(e)}")
    
    # Load all required data
        movement_df = load_movement_data_from_database(conn)
    jobs_df = pd.read_sql_query("SELECT * FROM jobs", conn)
    positions_df = pd.read_sql_query("SELECT * FROM positions", conn)
    
    # Try to load workforce context
    try:
        workforce_context_df = pd.read_sql_query("SELECT * FROM workforce_context", conn)
        print(f"🏢 Loaded workforce context: {len(workforce_context_df):,} records")
    except:
        workforce_context_df = pd.DataFrame()
        print("⚠️  Workforce context not available, using positions data only")
    
    print(f"🏢 Loaded jobs data: {len(jobs_df):,} job profiles")
    print(f"🏢 Loaded positions data: {len(positions_df):,} position records")
    print_memory_status()
    
    # =============================================================================
    # 2. ENHANCED DATA ENRICHMENT
    # =============================================================================
    
    print_section_header("ENHANCED DATA ENRICHMENT")
    print_methodology("""
    Enhanced data enrichment with expanded context:
    1. Create clean position-to-context mapping
    2. Enrich movements with job architecture
    3. Add organisational context (division, business unit, salary group)
    4. Include employment context (employee group)
    5. Memory-efficient chunked processing
    """)
    
    # Enhanced data enrichment
    movements_df = enrich_movement_data_with_context(movement_df, jobs_df, positions_df, workforce_context_df)
    
    print(f"✅ Enhanced enriched dataset: {len(movements_df):,} movement records")
    print_memory_status()
    
    # =============================================================================
    # 3. FEATURE PREPARATION
    # =============================================================================
    
    print_section_header("ENHANCED FEATURE PREPARATION")
    
    # Collect all available features and targets
    all_features = []
    for category_features in ENHANCED_FEATURES.values():
        all_features.extend(category_features)
    
    all_targets = []
    for category_targets in ENHANCED_TARGETS.values():
        all_targets.extend(category_targets)
    
    # Filter to available columns
    available_features = [f for f in all_features if f in movements_df.columns]
    available_targets = [t for t in all_targets if t in movements_df.columns]
    
    print(f"🔍 Available features ({len(available_features)}):")
    for category, features in ENHANCED_FEATURES.items():
        available_in_category = [f for f in features if f in available_features]
        if available_in_category:
            print(f"   → {category}: {available_in_category}")
    
    print(f"🎯 Available targets ({len(available_targets)}):")
    for category, targets in ENHANCED_TARGETS.items():
        available_in_category = [t for t in targets if t in available_targets]
        if available_in_category:
            print(f"   → {category}: {available_in_category}")
    
    # Apply data cleaning
    print("🔄 Applying enhanced data cleaning...")
    clean_movements = create_clean_movement_dataset(movements_df, jobs_df)
    
    # Filter to analysis columns
    analysis_cols = available_features + available_targets
    clean_movements = clean_movements.dropna(subset=analysis_cols)
    
    print(f"📊 Final dataset for analysis: {len(clean_movements):,} records")
    
    if len(clean_movements) == 0:
        raise ValueError("No valid records found for analysis after cleaning")
    
    # Encode categorical variables
    print("🔄 Encoding categorical variables...")
    label_encoders = {}
    encoded_data = clean_movements.copy()
    
    for col in analysis_cols:
        print(f"   → Encoding {col}...")
        encoded_values, le = safe_label_encoding(clean_movements, col)
        encoded_data[f'{col}_encoded'] = encoded_values
        label_encoders[col] = le
    
    print_memory_status()
    
    # =============================================================================
    # 4. UNIVARIATE ANALYSIS
    # =============================================================================
    
    univariate_results = perform_univariate_analysis(encoded_data, available_features, available_targets)
    
    # =============================================================================
    # 5. MULTIVARIATE ANALYSIS
    # =============================================================================
    
    multivariate_results = perform_multivariate_analysis(encoded_data, available_features, available_targets)
    
    # =============================================================================
    # 6. COMPREHENSIVE RESULTS SUMMARY
    # =============================================================================

    print_section_header("COMPREHENSIVE ANALYSIS RESULTS")
    
    # Univariate insights
    if not univariate_results.empty:
        print("🔍 TOP UNIVARIATE PREDICTORS:")
        print("-" * 60)
        
        # Best single predictors overall
        top_univariate = univariate_results.nlargest(10, 'accuracy')
        for _, row in top_univariate.iterrows():
            print(f"   {row['feature']:<35} → {row['target']:<25} Acc: {row['accuracy']:.3f}")
        
        # Best predictors by category
        print(f"\n📊 BEST PREDICTORS BY FEATURE CATEGORY:")
        for category in univariate_results['feature_category'].unique():
            if category != 'Other':
                category_best = univariate_results[univariate_results['feature_category'] == category].nlargest(3, 'accuracy')
                print(f"\n   🏆 {category}:")
                for _, row in category_best.iterrows():
                    print(f"      {row['feature']:<30} → {row['target']:<20} Acc: {row['accuracy']:.3f}")
    
    # Multivariate insights
    if not multivariate_results.empty:
        print(f"\n🔍 TOP MULTIVARIATE COMBINATIONS:")
        print("-" * 80)
        
        # Best combinations overall
        top_multivariate = multivariate_results.nlargest(10, 'accuracy')
        for _, row in top_multivariate.iterrows():
            print(f"   {row['feature_set']:<20} + {row['algorithm']:<20} → {row['target']:<20} Acc: {row['accuracy']:.3f}")
        
        # Best by feature set
        print(f"\n📊 BEST PERFORMANCE BY FEATURE SET:")
        for feature_set in multivariate_results['feature_set'].unique():
            set_best = multivariate_results[multivariate_results['feature_set'] == feature_set].nlargest(1, 'accuracy')
            if not set_best.empty:
                row = set_best.iloc[0]
                print(f"   {feature_set:<20}: {row['algorithm']:<20} Acc: {row['accuracy']:.3f}")
    
    # Key insights
    print(f"\n🎯 KEY INSIGHTS:")
            print("-" * 50)
            
    if not univariate_results.empty:
        best_single = univariate_results.loc[univariate_results['accuracy'].idxmax()]
        print(f"   → Best single predictor: {best_single['feature']} → {best_single['target']} ({best_single['accuracy']:.3f})")
    
    if not multivariate_results.empty:
        best_multi = multivariate_results.loc[multivariate_results['accuracy'].idxmax()]
        print(f"   → Best combination: {best_multi['feature_set']} + {best_multi['algorithm']} ({best_multi['accuracy']:.3f})")
    
    print(f"   → Total feature-target combinations tested: {len(univariate_results):,}")
    print(f"   → Total multivariate combinations tested: {len(multivariate_results):,}")
    
    print_memory_status()
    
    # Close database connection
    conn.close()
    print(f"\n🔒 Database connection closed")
    
    return {
        'univariate_results': univariate_results,
        'multivariate_results': multivariate_results,
        'feature_summary': {
            'available_features': available_features,
            'available_targets': available_targets,
            'total_records': len(clean_movements)
        }
    }

if __name__ == "__main__":
    results = main()
    print(f"\n{'='*80}")
    print("ENHANCED PREDICTIVE ANALYSIS COMPLETE")
    print(f"{'='*80}") 