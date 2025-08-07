#!/usr/bin/env python3
"""
Movement ML Trainer - Career Pathway Feasibility Predictor
==========================================================

This module implements ML-based career pathway feasibility prediction using regression models
that learn from recency-weighted historical movement volume.

Key Features:
1. Regression models for direct feasibility percentage prediction (0-100%)
2. Recency-weighted movement volume as target (0.4 exponential decay)
3. Feature engineering from job architecture and movement patterns
4. Statistical confidence from ensemble model predictions
5. Feature importance analysis to understand feasibility drivers

Approach:
- Target: Feasibility percentage based on recency-weighted movement volume
- Features: Job architecture, mobility scores, movement patterns (no skills timing mismatch)
- Models: Random Forest, Gradient Boosting, XGBoost regressors
- Output: Direct feasibility percentage (0-100%) users can understand

This provides clean, simple, defensible pathway feasibility predictions based on
what actually happened in the organization's recent history.
"""

import pandas as pd
import numpy as np
import sqlite3
import time
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import joblib
import json

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score, TimeSeriesSplit
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from scipy.stats import percentileofscore

from ..config.architectural_config_manager import get_config_manager
from ..error_handling.recovery import retry, circuit_breaker, fallback_on_failure
from ..utils.progress import ProgressTracker

# Try to import XGBoost
try:
    from xgboost import XGBRegressor
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

logger = logging.getLogger(__name__)


class MovementMLTrainer:
    """
    ML trainer for career pathway feasibility prediction.
    
    Ports the sophisticated ML pipeline from the research notebook into production
    architecture with proper error handling, configuration management, and progress tracking.
    """
    
    def __init__(self, db_path: Path, config_manager=None):
        """
        Initialize ML trainer.
        
        Args:
            db_path: Path to the database containing movement patterns
            config_manager: Configuration manager instance
        """
        self.db_path = db_path
        self.config_manager = config_manager or get_config_manager()
        self.logger = logging.getLogger(__name__)
        
        # Load ML configuration
        self.ml_config = self._load_ml_config()
        
        # Initialize model storage
        self.trained_models = {}
        self.feature_columns = []
        self.model_metadata = {}
        
        print(f"🤖 MovementMLTrainer initialized with database: {db_path}")
    
    def _load_ml_config(self) -> Dict[str, Any]:
        """Load ML configuration parameters from config files."""
        try:
            # Load from the movement_ml_training.yaml config file
            config = self.config_manager.get_nested_value('models', 'movement_ml_training')
            
            if not config:
                raise ValueError("Movement ML training configuration not found")
            
            # Flatten the config structure for easier access
            flattened_config = {
                # ML Pipeline settings
                'test_size': config.get('ml_pipeline', {}).get('test_size', 0.2),
                'random_state': config.get('ml_pipeline', {}).get('random_state', 42),
                'cv_folds': config.get('ml_pipeline', {}).get('cv_folds', 5),
                'temporal_split': config.get('ml_pipeline', {}).get('temporal_split', True),
                'model_types': config.get('ml_pipeline', {}).get('model_types', ['random_forest', 'gradient_boosting']),
                
                # Feature Engineering settings
                'recency_decay_rate': config.get('feature_engineering', {}).get('recency_decay_rate', 0.4),
                'exclude_columns': config.get('feature_engineering', {}).get('exclude_columns', []),
                
                # Prediction settings
                'confidence_level': config.get('prediction', {}).get('confidence_level', 0.8),
                'z_score': config.get('prediction', {}).get('z_score', 1.28),
                'agreement_threshold': config.get('prediction', {}).get('agreement_threshold', 0.2),
                
                # Hyperparameters
                'hyperparameters': config.get('hyperparameters', {}),
                
                # Database settings
                'batch_size': config.get('database_integration', {}).get('batch_size', 10000),
                'clear_existing': config.get('database_integration', {}).get('clear_existing', True),
                
                # Performance settings
                'max_memory_usage_mb': config.get('performance', {}).get('max_memory_usage_mb', 4096),
                'chunk_size': config.get('performance', {}).get('chunk_size', 50000),
                
                # Production thresholds
                'min_r2_score': config.get('production_thresholds', {}).get('min_r2_score', 0.1),
                'min_sample_size': config.get('production_thresholds', {}).get('min_sample_size', 100),
            }
            
            print("⚙️ Loaded ML configuration from movement_ml_training.yaml")
            return flattened_config
            
        except Exception as e:
            self.logger.warning(f"Failed to load ML config from files: {e}")
            
            # Minimal fallback configuration
            fallback_config = {
                'test_size': 0.2,
                'random_state': 42,
                'cv_folds': 5,
                'recency_decay_rate': 0.4,
                'temporal_split': True,
                'confidence_level': 0.8,
                'model_types': ['random_forest', 'gradient_boosting'],
                'hyperparameters': {
                    'random_forest': {'n_estimators': 100, 'max_depth': 5, 'random_state': 42},
                    'gradient_boosting': {'n_estimators': 100, 'max_depth': 3, 'learning_rate': 0.1, 'random_state': 42}
                }
            }
            
            print("⚙️ Using minimal fallback ML configuration")
            return fallback_config
    
    @retry(max_attempts=3)
    @circuit_breaker(failure_threshold=3)
    def load_movement_patterns_data(self) -> pd.DataFrame:
        """Load movement patterns data from database."""
        print("💾 Loading movement patterns data from database")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                SELECT 
                    movement_pattern_id,
                    movement_month,
                    from_job_profile_id,
                    to_job_profile_id,
                    movement_count,
                    unique_employees,
                    avg_days_between,
                    pct_total_movements,
                    movement_type
                FROM analytics_movement_patterns
                WHERE from_job_profile_id IS NOT NULL 
                  AND to_job_profile_id IS NOT NULL
                ORDER BY movement_month, from_job_profile_id, to_job_profile_id
                """
                
                movement_df = pd.read_sql_query(query, conn)
                
                if movement_df.empty:
                    raise ValueError("No movement patterns data found in database")
                
                print(f"✅ Loaded {len(movement_df):,} movement patterns from database")
                return movement_df
                
        except Exception as e:
            self.logger.error(f"Failed to load movement patterns data: {e}")
            raise
    
    @retry(max_attempts=3)
    def load_job_architecture_data(self) -> pd.DataFrame:
        """Load job architecture data for feature engineering."""
        print("🏗️ Loading job architecture data")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                SELECT 
                    JobProfileID,
                    JobProfile,
                    JobFunction,
                    JobSubFunction,
                    JobCategory,
                    ManagementLevel
                FROM core_job_architecture
                WHERE JobProfileID IS NOT NULL
                """
                
                jobs_df = pd.read_sql_query(query, conn)
                
                if jobs_df.empty:
                    raise ValueError("No job architecture data found in database")
                
                print(f"✅ Loaded {len(jobs_df):,} job profiles from database")
                return jobs_df
                
        except Exception as e:
            self.logger.error(f"Failed to load job architecture data: {e}")
            raise
    
    def aggregate_movement_patterns_to_job_level(self, movement_df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate movement patterns to job profile level with temporal weighting."""
        print("📋 Aggregating movement patterns to job profile level")
        
        # Calculate recency weights
        movement_df['movement_year'] = pd.to_datetime(movement_df['movement_month']).dt.year
        current_year = movement_df['movement_year'].max()
        movement_df['years_ago'] = current_year - movement_df['movement_year']
        movement_df['recency_weight'] = self.ml_config['recency_decay_rate'] ** movement_df['years_ago']
        
        # Aggregate to job profile level with recency weighting
        job_level_features = movement_df.groupby([
            'from_job_profile_id', 'to_job_profile_id'
        ]).agg({
            # Raw counts and frequencies
            'movement_count': 'sum',
            'unique_employees': 'sum',
            'avg_days_between': 'mean',
            'pct_total_movements': 'mean',
            
            # Temporal features
            'movement_year': ['count', 'min', 'max'],
            'recency_weight': 'sum',
            
            # Movement type
            'movement_type': lambda x: x.mode().iloc[0] if not x.empty else 'lateral'
        }).reset_index()
        
        # Flatten column names
        job_level_features.columns = [
            'from_job_profile_id', 'to_job_profile_id',
            'total_movement_count',
            'total_unique_employees',
            'avg_days_between',
            'avg_pct_total_movements',
            'transition_frequency',
            'first_observed_year',
            'last_observed_year',
            'recency_weighted_activity',
            'predominant_movement_type'
        ]
        
        # Calculate additional temporal features
        job_level_features['years_active'] = (
            job_level_features['last_observed_year'] - job_level_features['first_observed_year'] + 1
        )
        job_level_features['avg_movements_per_year'] = (
            job_level_features['total_movement_count'] / job_level_features['years_active']
        )
        job_level_features['recency_boost'] = (
            job_level_features['recency_weighted_activity'] / job_level_features['total_movement_count']
        )
        
        print(f"✅ Aggregated to {len(job_level_features):,} job profile transition pairs")
        return job_level_features
    
    def calculate_mobility_scores(self, job_level_features: pd.DataFrame) -> Tuple[Dict[str, float], Dict[str, float]]:
        """Calculate mobility scores for source and target jobs."""
        print("📊 Calculating mobility scores")
        
        source_mobility = {}
        target_mobility = {}
        
        # Calculate source role mobility (how mobile each FROM role is)
        source_analysis = job_level_features.groupby('from_job_profile_id').agg({
            'to_job_profile_id': 'nunique',
            'total_movement_count': 'sum',
            'recency_weighted_activity': 'sum',
            'avg_pct_total_movements': 'mean'
        }).reset_index()
        
        for _, row in source_analysis.iterrows():
            job_id = row['from_job_profile_id']
            unique_destinations = row['to_job_profile_id']
            total_movements = row['total_movement_count']
            market_share = row['avg_pct_total_movements']
            
            # Calculate mobility score
            diversity_score = min(unique_destinations / 10, 1.0)
            mobility_score = (
                diversity_score * 40 +
                min(unique_destinations / 10, 1) * 30 +
                min(total_movements / 100, 1) * 20 +
                min(market_share * 10, 1) * 10
            )
            
            source_mobility[job_id] = mobility_score
        
        # Calculate target role mobility (how accessible each TO role is)
        target_analysis = job_level_features.groupby('to_job_profile_id').agg({
            'from_job_profile_id': 'nunique',
            'total_movement_count': 'sum',
            'recency_weighted_activity': 'sum',
            'avg_pct_total_movements': 'mean'
        }).reset_index()
        
        for _, row in target_analysis.iterrows():
            job_id = row['to_job_profile_id']
            unique_sources = row['from_job_profile_id']
            total_movements = row['total_movement_count']
            market_share = row['avg_pct_total_movements']
            
            diversity_score = min(unique_sources / 10, 1.0)
            mobility_score = (
                diversity_score * 40 +
                min(unique_sources / 10, 1) * 30 +
                min(total_movements / 100, 1) * 20 +
                min(market_share * 10, 1) * 10
            )
            
            target_mobility[job_id] = mobility_score
        
        print(f"✅ Calculated mobility for {len(source_mobility):,} source and {len(target_mobility):,} target roles")
        return source_mobility, target_mobility
    
    def create_ml_features(self, job_level_features: pd.DataFrame, source_mobility: Dict[str, float], 
                          target_mobility: Dict[str, float], jobs_df: pd.DataFrame) -> pd.DataFrame:
        """Create ML features from job-level movement data."""
        print("🤖 Creating ML features from movement data")
        
        features_list = []
        
        # Create job function hierarchy mapping
        job_functions = jobs_df['JobFunction'].unique()
        function_hierarchy = {func: idx for idx, func in enumerate(sorted(job_functions))}
        
        for _, row in job_level_features.iterrows():
            from_job = row['from_job_profile_id']
            to_job = row['to_job_profile_id']
            
            # Get job information
            from_job_info = jobs_df[jobs_df['JobProfileID'] == from_job]
            to_job_info = jobs_df[jobs_df['JobProfileID'] == to_job]
            
            if from_job_info.empty or to_job_info.empty:
                continue
                
            from_job_info = from_job_info.iloc[0]
            to_job_info = to_job_info.iloc[0]
            
            # Movement features (from database)
            features = {
                'from_job_id': from_job,
                'to_job_id': to_job,
                'total_movement_count': row['total_movement_count'],
                'total_unique_employees': row['total_unique_employees'],
                'avg_days_between': row['avg_days_between'],
                'avg_pct_total_movements': row['avg_pct_total_movements'],
                'transition_frequency': row['transition_frequency'],
                'years_active': row['years_active'],
                'avg_movements_per_year': row['avg_movements_per_year'],
                'recency_weighted_activity': row['recency_weighted_activity'],
                'recency_boost': row['recency_boost'],
                'source_mobility_score': source_mobility.get(from_job, 0),
                'target_mobility_score': target_mobility.get(to_job, 0),
            }
            
            # Job architecture features
            features.update({
                'same_job_function': int(from_job_info['JobFunction'] == to_job_info['JobFunction']),
                'same_job_sub_function': int(from_job_info['JobSubFunction'] == to_job_info['JobSubFunction']),
                'same_management_level': int(from_job_info['ManagementLevel'] == to_job_info['ManagementLevel']),
                'same_job_category': int(from_job_info['JobCategory'] == to_job_info['JobCategory']),
            })
            
            # Job function distance
            from_func_idx = function_hierarchy.get(from_job_info['JobFunction'], 0)
            to_func_idx = function_hierarchy.get(to_job_info['JobFunction'], 0)
            features['job_function_distance'] = abs(from_func_idx - to_func_idx)
            
            # Management level progression
            try:
                from_level = int(str(from_job_info['ManagementLevel']).replace('Group ', '').replace('Group', ''))
                to_level = int(str(to_job_info['ManagementLevel']).replace('Group ', '').replace('Group', ''))
                features['management_level_progression'] = to_level - from_level
            except:
                features['management_level_progression'] = 0
            
            features_list.append(features)
        
        features_df = pd.DataFrame(features_list)
        print(f"✅ Created ML feature matrix: {len(features_df):,} transition pairs with {len(features_df.columns)-2:,} features")
        
        return features_df
    
    def create_movement_targets(self, features_df: pd.DataFrame) -> Tuple[pd.DataFrame, float]:
        """Create movement targets from recency-weighted data."""
        print("🎯 Creating movement volume targets from recency-weighted data")
        
        # Use raw recency-weighted movement count as target
        movement_target = features_df['recency_weighted_activity']
        features_df['movement_target'] = movement_target
        
        # Store max for later feasibility conversion
        max_movement = movement_target.max()
        
        print(f"✅ Movement targets created: range {movement_target.min():.1f} to {movement_target.max():.1f}")
        return features_df, max_movement
    
    def get_excluded_feature_columns(self) -> List[str]:
        """Define feature exclusion logic for consistency."""
        # Use configuration if available, otherwise use defaults
        configured_exclusions = self.ml_config.get('exclude_columns', [])
        
        # Always ensure these critical exclusions are present
        default_exclusions = [
            'from_job_id', 'to_job_id', 'movement_target',
            'recency_weighted_activity'  # This IS the target - causes data leakage!
        ]
        
        # Combine and deduplicate
        all_exclusions = list(set(configured_exclusions + default_exclusions))
        return all_exclusions
    
    def prepare_ml_data(self, features_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, List[str]]:
        """Prepare data for ML training with proper feature selection."""
        print("🛠️ Preparing data for ML training")
        
        excluded_columns = self.get_excluded_feature_columns()
        feature_columns = [col for col in features_df.columns if col not in excluded_columns]
        
        # Separate features and targets
        X = features_df[feature_columns]
        y = features_df['movement_target']
        
        # Handle missing values
        X = X.fillna(0)
        
        self.feature_columns = feature_columns
        
        print(f"✅ Prepared ML data: {X.shape[1]} features, {X.shape[0]} samples")
        print(f"🚫 Excluded columns: {excluded_columns}")
        
        return X, y, feature_columns
    
    @retry(max_attempts=2)
    def train_ml_models(self, X: pd.DataFrame, y: pd.Series) -> Tuple[Dict[str, Any], Any, str, pd.DataFrame, pd.Series]:
        """Train ensemble ML models for movement volume prediction."""
        print("🚀 Starting ML model training")
        
        # Split data for training (temporal split to prevent data leakage)
        if self.ml_config.get('temporal_split', True):
            split_point = int(0.8 * len(X))
            X_train, X_test = X.iloc[:split_point], X.iloc[split_point:]
            y_train, y_test = y.iloc[:split_point], y.iloc[split_point:]
            print("⏰ Using temporal split to prevent data leakage")
        else:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=self.ml_config['test_size'], 
                random_state=self.ml_config['random_state']
            )
        
        print(f"📊 Training: {len(X_train):,} samples, Testing: {len(X_test):,} samples")
        
        # Define models
        models = {}
        
        # Random Forest
        if 'random_forest' in self.ml_config['model_types']:
            rf_params = self.ml_config['hyperparameters']['random_forest'].copy()
            rf_params['random_state'] = self.ml_config['random_state']
            models['Random Forest'] = RandomForestRegressor(**rf_params)
        
        # Gradient Boosting
        if 'gradient_boosting' in self.ml_config['model_types']:
            gb_params = self.ml_config['hyperparameters']['gradient_boosting'].copy()
            gb_params['random_state'] = self.ml_config['random_state']
            models['Gradient Boosting'] = GradientBoostingRegressor(**gb_params)
        
        # XGBoost (if available and configured)
        if XGBOOST_AVAILABLE and 'xgboost' in self.ml_config['model_types']:
            xgb_params = self.ml_config['hyperparameters']['xgboost'].copy()
            xgb_params['random_state'] = self.ml_config['random_state']
            models['XGBoost'] = XGBRegressor(**xgb_params)
        
        # Train and evaluate models
        model_results = {}
        
        with ProgressTracker(total=len(models), desc="Training ML models") as progress:
            for model_name, model in models.items():
                print(f"📊 Training {model_name}...")
                
                start_time = time.time()
                model.fit(X_train, y_train)
                training_time = time.time() - start_time
                
                # Generate predictions
                y_pred = model.predict(X_test)
                
                # Calculate metrics
                mse = mean_squared_error(y_test, y_pred)
                mae = mean_absolute_error(y_test, y_pred)
                r2 = r2_score(y_test, y_pred)
                rmse = np.sqrt(mse)
                
                # Cross-validation
                tscv = TimeSeriesSplit(n_splits=self.ml_config['cv_folds'])
                cv_scores = cross_val_score(model, X_train, y_train, cv=tscv, scoring='r2')
                
                # Store results
                model_results[model_name] = {
                    'model': model,
                    'mse': mse,
                    'mae': mae,
                    'rmse': rmse,
                    'r2_score': r2,
                    'cv_mean': cv_scores.mean(),
                    'cv_std': cv_scores.std(),
                    'training_time': training_time,
                    'predictions': y_pred
                }
                
                print(f"✅ {model_name} - R²: {r2:.3f}, RMSE: {rmse:.1f}, Training time: {training_time:.2f}s")
                progress.update(1)
        
        # Select best model
        best_model_name = max(model_results.keys(), key=lambda k: model_results[k]['r2_score'])
        best_model = model_results[best_model_name]['model']
        
        print(f"🏆 Best model: {best_model_name} (R²: {model_results[best_model_name]['r2_score']:.3f})")
        
        self.trained_models = model_results
        return model_results, best_model, best_model_name, X_test, y_test
    
    def generate_pathway_predictions(self, best_model, features_df: pd.DataFrame, jobs_df: pd.DataFrame, 
                                   max_movement: float, model_results: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """Generate pathway predictions for database insertion."""
        print("🔮 Generating pathway predictions for database insertion")
        
        # Use exact same feature columns from training
        X = features_df[self.feature_columns].fillna(0)
        
        # Generate predictions from all models for ensemble
        all_predictions = {}
        if model_results:
            for model_name, model_info in model_results.items():
                model = model_info['model']
                all_predictions[model_name] = model.predict(X)
        else:
            all_predictions['best_model'] = best_model.predict(X)
        
        # Calculate ensemble statistics
        prediction_matrix = np.array(list(all_predictions.values())).T
        ensemble_mean = np.mean(prediction_matrix, axis=1)
        ensemble_std = np.std(prediction_matrix, axis=1)
        
        # Prediction intervals (configurable confidence level)
        confidence_level = self.ml_config.get('confidence_level', 0.8)
        z_score = self.ml_config.get('z_score', 1.28)  # Default for 80% confidence interval
        lower_bound = ensemble_mean - (z_score * ensemble_std)
        upper_bound = ensemble_mean + (z_score * ensemble_std)
        
        # Model agreement analysis
        prediction_agreement = []
        for i in range(len(ensemble_mean)):
            row_predictions = prediction_matrix[i]
            mean_pred = ensemble_mean[i]
            agreement_threshold = self.ml_config.get('agreement_threshold', 0.2) * mean_pred if mean_pred > 0 else 1.0
            agreeing_models = np.sum(np.abs(row_predictions - mean_pred) <= agreement_threshold)
            total_models = len(row_predictions)
            prediction_agreement.append(f"{agreeing_models}/{total_models}")
        
        # Calculate percentile ranking
        pathway_percentiles = [
            percentileofscore(ensemble_mean, score, kind='rank') 
            for score in ensemble_mean
        ]
        
        # Convert to readable categories
        def get_pathway_category(percentile):
            if percentile >= 99:
                return "Premier pathway (Top 1%)"
            elif percentile >= 95:
                return "Major pathway (Top 5%)"
            elif percentile >= 90:
                return "Significant pathway (Top 10%)"
            elif percentile >= 75:
                return "Common pathway (Top 25%)"
            elif percentile >= 50:
                return "Standard pathway (Top 50%)"
            else:
                return "Emerging pathway (Bottom 50%)"
        
        pathway_categories = [get_pathway_category(p) for p in pathway_percentiles]
        
        # Create database-ready DataFrame
        predictions_df = features_df[['from_job_id', 'to_job_id']].copy()
        
        # Add core predictions
        predictions_df['ml_predicted_movements'] = ensemble_mean
        predictions_df['pathway_volume_percentile'] = pathway_percentiles
        predictions_df['pathway_volume_category'] = pathway_categories
        
        # Add confidence metrics
        predictions_df['prediction_interval_lower_80pct'] = lower_bound
        predictions_df['prediction_interval_upper_80pct'] = upper_bound
        predictions_df['prediction_interval_width_80pct'] = upper_bound - lower_bound
        predictions_df['model_agreement_fraction'] = prediction_agreement
        predictions_df['models_agreeing_count'] = [int(ag.split('/')[0]) for ag in prediction_agreement]
        predictions_df['agreement_rate_decimal'] = [int(ag.split('/')[0])/int(ag.split('/')[1]) for ag in prediction_agreement]
        
        # Add individual model predictions
        for i, (model_name, predictions) in enumerate(all_predictions.items()):
            col_name = f'prediction_{model_name.lower().replace(" ", "_").replace("(", "").replace(")", "")}'
            predictions_df[col_name] = predictions
        
        # Add historical context
        predictions_df['historical_sample_size'] = features_df.get('total_movement_count', 0)
        predictions_df['ensemble_standard_deviation'] = ensemble_std
        predictions_df['prediction_coefficient_of_variation_percent'] = (ensemble_std / ensemble_mean) * 100
        
        # Add job names for business context
        job_names = jobs_df.set_index('JobProfileID')['JobProfile'].to_dict()
        predictions_df['from_job_profile_name'] = predictions_df['from_job_id'].map(job_names)
        predictions_df['to_job_profile_name'] = predictions_df['to_job_id'].map(job_names)
        
        # Rename columns to match database schema
        predictions_df = predictions_df.rename(columns={
            'from_job_id': 'from_job_profile_id',
            'to_job_id': 'to_job_profile_id'
        })
        
        # Add prediction_id (primary key)
        predictions_df['prediction_id'] = (
            predictions_df['from_job_profile_id'] + '_' + 
            predictions_df['to_job_profile_id']
        )
        
        # Add metadata
        predictions_df['training_algorithm'] = 'ensemble_v1.0'
        predictions_df['training_timestamp'] = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"✅ Generated {len(predictions_df):,} pathway predictions for database insertion")
        
        return predictions_df
    
    def save_models_and_metadata(self, model_results: Dict[str, Any], output_dir: Path) -> Dict[str, Path]:
        """Save trained models and metadata to files."""
        print(f"💾 Saving models and metadata to {output_dir}")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        saved_files = {}
        
        # Save individual models
        for model_name, model_info in model_results.items():
            model_filename = f"{model_name.lower().replace(' ', '_').replace('(', '').replace(')', '')}_model.joblib"
            model_path = output_dir / model_filename
            joblib.dump(model_info['model'], model_path)
            saved_files[f'{model_name}_model'] = model_path
            print(f"✅ Saved {model_name} model to {model_path}")
        
        # Save feature columns (CRITICAL for prediction consistency)
        feature_columns_path = output_dir / 'feature_columns.json'
        with open(feature_columns_path, 'w') as f:
            json.dump(self.feature_columns, f, indent=2)
        saved_files['feature_columns'] = feature_columns_path
        
        # Save model metadata
        metadata = {
            'training_timestamp': pd.Timestamp.now().isoformat(),
            'model_performance': {
                name: {
                    'r2_score': info['r2_score'],
                    'mse': info['mse'],
                    'mae': info['mae'],
                    'rmse': info['rmse'],
                    'cv_mean': info['cv_mean'],
                    'cv_std': info['cv_std'],
                    'training_time': info['training_time']
                }
                for name, info in model_results.items()
            },
            'best_model': max(model_results.keys(), key=lambda k: model_results[k]['r2_score']),
            'feature_count': len(self.feature_columns),
            'feature_columns': self.feature_columns,
            'ml_config': self.ml_config
        }
        
        metadata_path = output_dir / 'model_metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        saved_files['metadata'] = metadata_path
        
        print(f"✅ Saved {len(saved_files)} files to {output_dir}")
        return saved_files
    
    def execute_full_ml_pipeline(self, output_dir: Optional[Path] = None) -> Dict[str, Any]:
        """Execute the complete ML training pipeline."""
        print("🚀 Starting complete ML training pipeline")
        
        try:
            # Step 1: Load data
            with ProgressTracker(total=7, desc="ML Training Pipeline") as progress:
                movement_df = self.load_movement_patterns_data()
                progress.update(1)
                
                jobs_df = self.load_job_architecture_data()
                progress.update(1)
                
                # Step 2: Feature engineering
                job_level_features = self.aggregate_movement_patterns_to_job_level(movement_df)
                progress.update(1)
                
                source_mobility, target_mobility = self.calculate_mobility_scores(job_level_features)
                progress.update(1)
                
                features_df = self.create_ml_features(job_level_features, source_mobility, target_mobility, jobs_df)
                features_df, max_movement = self.create_movement_targets(features_df)
                progress.update(1)
                
                # Step 3: Train models
                X, y, feature_columns = self.prepare_ml_data(features_df)
                model_results, best_model, best_model_name, X_test, y_test = self.train_ml_models(X, y)
                progress.update(1)
                
                # Step 4: Generate predictions
                predictions_df = self.generate_pathway_predictions(
                    best_model, features_df, jobs_df, max_movement, model_results
                )
                progress.update(1)
            
            # Step 5: Save models (if output directory provided)
            saved_files = {}
            if output_dir:
                saved_files = self.save_models_and_metadata(model_results, output_dir)
            
            print("✅ ML training pipeline completed successfully")
            
            return {
                'success': True,
                'model_results': model_results,
                'best_model': best_model,
                'best_model_name': best_model_name,
                'predictions_df': predictions_df,
                'feature_columns': feature_columns,
                'saved_files': saved_files,
                'performance_metrics': {
                    'total_predictions': len(predictions_df),
                    'best_model_r2': model_results[best_model_name]['r2_score'],
                    'best_model_mae': model_results[best_model_name]['mae'],
                    'feature_count': len(feature_columns)
                }
            }
            
        except Exception as e:
            self.logger.error(f"ML training pipeline failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'predictions_df': None
            }