#!/usr/bin/env python3
"""
Pathway Predictor - Production ML Prediction Engine
==================================================

This script provides proper ML-based career pathway predictions using the exact same
feature engineering pipeline as the training process, ensuring 1:1 consistency.

Key Features:
1. Reuses MovementMLTrainer modules for identical feature engineering
2. Loads trained joblib models with proper metadata
3. Queries production database using same SQL as training
4. Generates proper confidence distributions (not uniform 92.7%!)
5. Three prediction modes: Job A->B, Job A->many, full corpus analysis

Architecture:
- Imports and leverages existing src/ modules for feature engineering
- Uses production database schema correctly
- Applies trained models with ensemble confidence calculation
- Provides detailed reporting and analysis

Usage:
    python pathway_predictor.py --job-to-job --from-job "12345" --to-job "67890"
    python pathway_predictor.py --job-to-many --from-job "12345" --top-n 10
    python pathway_predictor.py --corpus-analysis --sample-size 1000
"""

import argparse
import sqlite3
import pandas as pd
import numpy as np
import joblib
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import time
from datetime import datetime
import sys
import logging

# Progress bar
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

# Import our existing modules for feature engineering
sys.path.append('src')
from skill_similarity_engine.models.movement_ml_trainer import MovementMLTrainer
from skill_similarity_engine.config.architectural_config_manager import get_config_manager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PathwayPredictor:
    """
    Production-ready pathway prediction engine that reuses training pipeline components.
    
    This class ensures 1:1 consistency between training and prediction by leveraging
    the exact same feature engineering modules used during ML model training.
    """
    
    def __init__(self, db_path: Optional[str] = None, models_dir: str = "models/2025-Q3"):
        """
        Initialize the pathway predictor.
        
        Args:
            db_path: Path to the production database (default: models/2025-Q3/business_context.sqlite)
            models_dir: Directory containing trained ML models
        """
        # Use default production database path if not specified
        if db_path is None:
            db_path = "models/2025-Q3/business_context.sqlite"
        
        self.db_path = Path(db_path)
        self.models_dir = Path(models_dir)
        
        # Initialize ML trainer for feature engineering (reuse existing modules!)
        self.ml_trainer = MovementMLTrainer(self.db_path)
        
        # Storage for loaded models and metadata
        self.trained_models = {}
        self.feature_columns = []
        self.model_metadata = {}
        
        # Cached data for efficiency (loaded once, reused for all predictions)
        self._cached_movement_df = None
        self._cached_jobs_df = None
        self._cached_job_level_features = None
        self._cached_source_mobility = None
        self._cached_target_mobility = None
        
        print(f"🔮 PathwayPredictor initialized - DB: {self.db_path.name}")
    
    def load_trained_models(self) -> bool:
        """Load trained ML models and metadata."""
        try:
            # Load model metadata - try both locations
            metadata_files = [
                self.models_dir / "model_metadata.json",  # In models directory
                Path("ml-training-metadata.json"),        # In root directory
                self.models_dir / "ml-training-metadata.json"  # Also try in models dir
            ]
            
            metadata_file = None
            for candidate in metadata_files:
                if candidate.exists():
                    metadata_file = candidate
                    break
            
            if metadata_file is None:
                raise FileNotFoundError(f"Model metadata not found in any of: {[str(f) for f in metadata_files]}")
            
            with open(metadata_file, 'r') as f:
                self.model_metadata = json.load(f)
                
            self.feature_columns = self.model_metadata.get('feature_columns', [])
            
            # Load individual model files
            model_files = {
                'Random Forest': 'random_forest_model.joblib',
                'Gradient Boosting': 'gradient_boosting_model.joblib', 
                'XGBoost': 'xgboost_model.joblib'
            }
            
            models_loaded = 0
            for model_name, filename in model_files.items():
                model_path = self.models_dir / filename
                if model_path.exists():
                    try:
                        self.trained_models[model_name] = joblib.load(model_path)
                        models_loaded += 1
                    except Exception as e:
                        print(f"⚠️  Failed to load {model_name}: {e}")
            
            if models_loaded == 0:
                raise RuntimeError("No ML models could be loaded")
            
            print(f"🤖 Loaded {models_loaded} ML models with {len(self.feature_columns)} features")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load trained models: {e}")
            return False
    
    def load_and_cache_data(self) -> bool:
        """Load and cache movement patterns and job data for efficient reuse."""
        try:
            # Suppress verbose output from ML trainer
            import logging
            ml_logger = logging.getLogger('skill_similarity_engine.models.movement_ml_trainer')
            original_level = ml_logger.level
            ml_logger.setLevel(logging.ERROR)
            
            print("📊 Loading movement patterns and job data...")
            
            # Load and cache all data
            self._cached_movement_df = self.ml_trainer.load_movement_patterns_data()
            self._cached_jobs_df = self.ml_trainer.load_job_architecture_data()
            self._cached_job_level_features = self.ml_trainer.aggregate_movement_patterns_to_job_level(self._cached_movement_df)
            self._cached_source_mobility, self._cached_target_mobility = self.ml_trainer.calculate_mobility_scores(self._cached_job_level_features)
            
            # Restore logging level
            ml_logger.setLevel(original_level)
            
            print(f"✅ Cached {len(self._cached_movement_df):,} movement patterns, {len(self._cached_jobs_df):,} jobs, {len(self._cached_job_level_features):,} job transitions")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load and cache data: {e}")
            return False
    
    def create_prediction_features(self, from_job_id: str, to_job_id: str) -> Optional[pd.DataFrame]:
        """
        Create features for a specific job transition using cached data for efficiency.
        
        This method reuses MovementMLTrainer's feature engineering to ensure 1:1 consistency.
        """
        try:
            # Use cached data instead of reloading every time
            if self._cached_job_level_features is None:
                raise RuntimeError("Data not cached. Call load_and_cache_data() first.")
            
            # Filter for the specific transition we want to predict
            transition_data = self._cached_job_level_features[
                (self._cached_job_level_features['from_job_profile_id'] == from_job_id) & 
                (self._cached_job_level_features['to_job_profile_id'] == to_job_id)
            ].copy()
            
            if transition_data.empty:
                # Create synthetic row for unseen transitions (silent)
                from_job_info = self._cached_jobs_df[self._cached_jobs_df['JobProfileID'] == from_job_id]
                to_job_info = self._cached_jobs_df[self._cached_jobs_df['JobProfileID'] == to_job_id]
                
                if from_job_info.empty or to_job_info.empty:
                    return None
                
                # Create synthetic transition with zero movement history
                synthetic_row = {
                    'from_job_profile_id': from_job_id,
                    'to_job_profile_id': to_job_id,
                    'total_movement_count': 0,
                    'total_unique_employees': 0,
                    'avg_days_between': 365.0,  # Default 1 year
                    'avg_pct_total_movements': 0.0,
                    'transition_frequency': 0,
                    'years_active': 1,
                    'avg_movements_per_year': 0.0,
                    'recency_weighted_activity': 0.0,
                    'recency_boost': 1.0
                }
                
                transition_data = pd.DataFrame([synthetic_row])
            
            # Create ML features using the exact same method as training (suppress output)
            import sys
            from io import StringIO
            
            # Capture stdout to suppress verbose output
            old_stdout = sys.stdout
            sys.stdout = StringIO()
            
            try:
                features_df = self.ml_trainer.create_ml_features(
                    transition_data, self._cached_source_mobility, self._cached_target_mobility, self._cached_jobs_df
                )
            finally:
                # Always restore stdout
                sys.stdout = old_stdout
            
            return features_df
            
        except Exception as e:
            logger.error(f"Failed to create prediction features: {e}")
            return None
    
    def predict_pathway_feasibility(self, from_job_id: str, to_job_id: str) -> Dict[str, Any]:
        """
        Predict pathway feasibility for a specific job transition.
        
        Returns:
            Dictionary with prediction results and confidence metrics
        """
        # Removed verbose prediction output
        
        # Create features using same pipeline as training
        features_df = self.create_prediction_features(from_job_id, to_job_id)
        
        if features_df is None or features_df.empty:
            return {
                'from_job_id': from_job_id,
                'to_job_id': to_job_id,
                'feasibility_percentage': 0.0,
                'confidence_score': 0.0,
                'prediction_status': 'failed',
                'error': 'Could not generate features'
            }
        
        try:
            # Prepare features in the same format as training
            feature_values = features_df[self.feature_columns].fillna(0)
            
            # Get predictions from all models
            model_predictions = {}
            raw_predictions = []
            
            for model_name, model in self.trained_models.items():
                try:
                    # Get raw prediction (movement volume)
                    raw_pred = model.predict(feature_values)[0]
                    model_predictions[model_name] = raw_pred
                    raw_predictions.append(raw_pred)
                    
                except Exception as e:
                    print(f"⚠️  {model_name} prediction failed: {e}")
                    continue
            
            if not raw_predictions:
                return {
                    'from_job_id': from_job_id,
                    'to_job_id': to_job_id,
                    'feasibility_percentage': 0.0,
                    'confidence_score': 0.0,
                    'prediction_status': 'failed',
                    'error': 'All model predictions failed'
                }
            
            # Calculate ensemble prediction
            ensemble_prediction = np.mean(raw_predictions)
            
            # Convert to feasibility percentage (using max from training metadata)
            max_movement = self.model_metadata.get('max_movement_volume', 100.0)
            feasibility_percentage = min(100.0, max(0.0, (ensemble_prediction / max_movement) * 100))
            
            # Calculate confidence from model agreement
            if len(raw_predictions) > 1:
                prediction_std = np.std(raw_predictions)
                prediction_mean = np.mean(raw_predictions)
                coefficient_of_variation = prediction_std / (prediction_mean + 1e-6)
                confidence_score = max(0.0, min(1.0, 1.0 - coefficient_of_variation))
            else:
                confidence_score = 0.5  # Medium confidence for single model
            
            return {
                'from_job_id': from_job_id,
                'to_job_id': to_job_id,
                'feasibility_percentage': round(feasibility_percentage, 2),
                'confidence_score': round(confidence_score, 3),
                'prediction_status': 'success',
                'model_predictions': model_predictions,
                'ensemble_raw_prediction': ensemble_prediction,
                'feature_count': len(self.feature_columns)
            }
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return {
                'from_job_id': from_job_id,
                'to_job_id': to_job_id,
                'feasibility_percentage': 0.0,
                'confidence_score': 0.0,
                'prediction_status': 'failed',
                'error': str(e)
            }
    
    def predict_job_to_many(self, from_job_id: str, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Predict feasibility from one job to many potential target jobs.
        
        Args:
            from_job_id: Source job profile ID
            top_n: Number of top predictions to return
            
        Returns:
            List of prediction results sorted by feasibility
        """
        try:
            # Get all possible target jobs from database
            with sqlite3.connect(self.db_path) as conn:
                query = """
                SELECT DISTINCT JobProfileID, JobProfile, JobFunction, ManagementLevel
                FROM core_job_architecture 
                WHERE JobProfileID != ?
                ORDER BY JobProfile
                """
                target_jobs_df = pd.read_sql_query(query, conn, params=[from_job_id])
            
            if target_jobs_df.empty:
                return []
            
            print(f"🎯 Processing {len(target_jobs_df)} job transitions...")
            
            # Predict for each target job with progress bar
            predictions = []
            
            if TQDM_AVAILABLE:
                target_jobs_iter = tqdm(target_jobs_df.iterrows(), total=len(target_jobs_df),
                                      desc="🎯 Job-to-many predictions", unit="jobs")
            else:
                target_jobs_iter = target_jobs_df.iterrows()
            
            for _, target_job in target_jobs_iter:
                to_job_id = target_job['JobProfileID']
                
                result = self.predict_pathway_feasibility(from_job_id, to_job_id)
                
                # Add job metadata
                result.update({
                    'to_job_title': target_job['JobProfile'],
                    'to_job_function': target_job['JobFunction'],
                    'to_job_management_level': target_job['ManagementLevel']
                })
                
                predictions.append(result)
            
            # Sort by feasibility and return top N
            predictions.sort(key=lambda x: x['feasibility_percentage'], reverse=True)
            
            print(f"✅ Completed {len(predictions)} predictions")
            return predictions[:top_n]
            
        except Exception as e:
            logger.error(f"Job-to-many prediction failed: {e}")
            return []
    
    def run_corpus_analysis(self, sample_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Run full corpus analysis predicting all job pairs against each other.
        
        Args:
            sample_size: If specified, randomly sample this many job pairs
            
        Returns:
            Dictionary with analysis results and statistics
        """
        try:
            # Get all job profiles
            with sqlite3.connect(self.db_path) as conn:
                query = """
                SELECT JobProfileID, JobProfile, JobFunction, ManagementLevel
                FROM core_job_architecture
                ORDER BY JobProfile
                """
                jobs_df = pd.read_sql_query(query, conn)
            
            # Generate all possible job pairs (Cartesian product)
            job_pairs = []
            for _, from_job in jobs_df.iterrows():
                for _, to_job in jobs_df.iterrows():
                    if from_job['JobProfileID'] != to_job['JobProfileID']:  # Skip self-transitions
                        job_pairs.append((from_job['JobProfileID'], to_job['JobProfileID']))
            
            total_pairs = len(job_pairs)
            
            # Sample if requested
            if sample_size and sample_size < total_pairs:
                import random
                job_pairs = random.sample(job_pairs, sample_size)
                
            print(f"🌐 Corpus Analysis: {len(jobs_df)} jobs → {len(job_pairs):,} transitions")
            
            # Run predictions with progress bar
            predictions = []
            start_time = time.time()
            
            if TQDM_AVAILABLE:
                # Use tqdm for clean progress bar
                job_pairs_iter = tqdm(job_pairs, desc="🔮 Predicting pathways", 
                                    unit="predictions", leave=True)
            else:
                # Fallback to basic iteration
                job_pairs_iter = job_pairs
                print("🔮 Processing predictions...")
            
            for from_job_id, to_job_id in job_pairs_iter:
                result = self.predict_pathway_feasibility(from_job_id, to_job_id)
                predictions.append(result)
            
            # Calculate statistics
            predictions_df = pd.DataFrame(predictions)
            successful_predictions = predictions_df[predictions_df['prediction_status'] == 'success']
            
            if len(successful_predictions) == 0:
                return {
                    'total_predictions': len(predictions),
                    'successful_predictions': 0,
                    'error': 'No successful predictions'
                }
            
            feasibility_scores = successful_predictions['feasibility_percentage']
            confidence_scores = successful_predictions['confidence_score']
            
            analysis_results = {
                'analysis_timestamp': datetime.now().isoformat(),
                'total_job_profiles': len(jobs_df),
                'total_predictions': len(predictions),
                'successful_predictions': len(successful_predictions),
                'failed_predictions': len(predictions) - len(successful_predictions),
                'success_rate': len(successful_predictions) / len(predictions),
                
                # Feasibility distribution
                'feasibility_stats': {
                    'mean': float(feasibility_scores.mean()),
                    'median': float(feasibility_scores.median()),
                    'std': float(feasibility_scores.std()),
                    'min': float(feasibility_scores.min()),
                    'max': float(feasibility_scores.max()),
                    'q25': float(feasibility_scores.quantile(0.25)),
                    'q75': float(feasibility_scores.quantile(0.75))
                },
                
                # Confidence distribution
                'confidence_stats': {
                    'mean': float(confidence_scores.mean()),
                    'median': float(confidence_scores.median()),
                    'std': float(confidence_scores.std()),
                    'min': float(confidence_scores.min()),
                    'max': float(confidence_scores.max()),
                    'q25': float(confidence_scores.quantile(0.25)),
                    'q75': float(confidence_scores.quantile(0.75))
                },
                
                # Model metadata
                'model_info': {
                    'feature_columns_count': len(self.feature_columns),
                    'models_used': list(self.trained_models.keys()),
                    'training_metadata': self.model_metadata
                }
            }
            
            # Print comprehensive distribution analysis
            self._print_distribution_analysis(analysis_results, time.time() - start_time)
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"Corpus analysis failed: {e}")
            return {'error': str(e)}
    
    def _print_distribution_analysis(self, results: Dict[str, Any], elapsed_time: float) -> None:
        """Print comprehensive distribution analysis."""
        print(f"\n{'='*80}")
        print(f"🎯 PATHWAY PREDICTION ANALYSIS RESULTS")
        print(f"{'='*80}")
        
        # Summary statistics
        print(f"📊 SUMMARY:")
        print(f"   • Job Profiles: {results['total_job_profiles']:,}")
        print(f"   • Total Predictions: {results['total_predictions']:,}")
        print(f"   • Successful: {results['successful_predictions']:,} ({results['success_rate']*100:.1f}%)")
        print(f"   • Failed: {results['failed_predictions']:,}")
        print(f"   • Processing Time: {elapsed_time:.1f} seconds")
        print(f"   • Rate: {results['total_predictions']/elapsed_time:.1f} predictions/sec")
        
        # Feasibility distribution
        feas = results['feasibility_stats']
        print(f"\n📈 FEASIBILITY DISTRIBUTION (%):")
        print(f"   • Mean: {feas['mean']:.2f}%")
        print(f"   • Median: {feas['median']:.2f}%") 
        print(f"   • Std Dev: {feas['std']:.3f}")
        print(f"   • Range: {feas['min']:.2f}% - {feas['max']:.2f}%")
        print(f"   • Q25-Q75: {feas['q25']:.2f}% - {feas['q75']:.2f}%")
        
        # Confidence distribution  
        conf = results['confidence_stats']
        print(f"\n🎯 CONFIDENCE DISTRIBUTION:")
        print(f"   • Mean: {conf['mean']:.4f} ({conf['mean']*100:.2f}%)")
        print(f"   • Median: {conf['median']:.4f} ({conf['median']*100:.2f}%)")
        print(f"   • Std Dev: {conf['std']:.6f}")
        print(f"   • Range: {conf['min']:.4f} - {conf['max']:.4f}")
        print(f"   • Q25-Q75: {conf['q25']:.4f} - {conf['q75']:.4f}")
        
        # Model information
        model_info = results['model_info']
        print(f"\n🤖 MODEL INFORMATION:")
        print(f"   • Models Used: {', '.join(model_info['models_used'])}")
        print(f"   • Feature Count: {model_info['feature_columns_count']}")
        
        # Training performance (if available)
        if 'training_metadata' in model_info and 'model_performance' in model_info['training_metadata']:
            perf = model_info['training_metadata']['model_performance']
            print(f"\n📊 TRAINING PERFORMANCE:")
            for model_name, metrics in perf.items():
                if 'r2_score' in metrics:
                    print(f"   • {model_name}: R² = {metrics['r2_score']:.4f}")
        
        # Distribution quality assessment
        print(f"\n✅ QUALITY ASSESSMENT:")
        
        # Check for uniform confidence (the original problem)
        if conf['std'] < 0.001:
            print(f"   ⚠️  WARNING: Very low confidence variation (std={conf['std']:.6f})")
            print(f"      This may indicate model issues or uniform predictions")
        else:
            print(f"   ✅ Confidence variation is healthy (std={conf['std']:.6f})")
            
        # Check feasibility range
        if feas['max'] - feas['min'] < 0.1:
            print(f"   ⚠️  WARNING: Very narrow feasibility range ({feas['min']:.2f}% - {feas['max']:.2f}%)")
        else:
            print(f"   ✅ Feasibility range is appropriate ({feas['min']:.2f}% - {feas['max']:.2f}%)")
            
        # Success rate assessment
        if results['success_rate'] < 0.95:
            print(f"   ⚠️  WARNING: Low success rate ({results['success_rate']*100:.1f}%)")
        else:
            print(f"   ✅ High prediction success rate ({results['success_rate']*100:.1f}%)")
            
        print(f"{'='*80}\n")
    
    def run_sanity_checks(self, sample_size: Optional[int] = None, threshold: float = 2.0, 
                         check_categories: List[str] = None) -> Dict[str, Any]:
        """
        Run reality sanity checks on pathway predictions to identify unrealistic scenarios.
        
        Args:
            sample_size: Number of predictions to analyze (default: 1000)
            threshold: Threshold for flagging unrealistic movement volumes
            check_categories: List of sanity check categories to perform
            
        Returns:
            Dictionary with sanity check results and flagged scenarios
        """
        if check_categories is None:
            check_categories = ['management_demotions', 'cross_function_jumps', 'unrealistic_volume']
        
        if sample_size is None:
            sample_size = 1000
            
        print(f"🧠 PATHWAY SANITY CHECK ANALYSIS")
        print(f"{'='*80}")
        print(f"📊 Sample Size: {sample_size:,} predictions")
        print(f"🚨 Volume Threshold: {threshold} movements/year")
        print(f"🔍 Check Categories: {', '.join(check_categories)}")
        print(f"{'='*80}\n")
        
        try:
            # Get job pairs for analysis
            with sqlite3.connect(self.db_path) as conn:
                query = """
                SELECT JobProfileID, JobProfile, JobFunction, JobSubFunction, 
                       ManagementLevel, JobCategory
                FROM core_job_architecture
                ORDER BY JobProfile
                """
                jobs_df = pd.read_sql_query(query, conn)
            
            # Generate sample job pairs
            job_pairs = []
            for _, from_job in jobs_df.iterrows():
                for _, to_job in jobs_df.iterrows():
                    if from_job['JobProfileID'] != to_job['JobProfileID']:
                        job_pairs.append((from_job, to_job))
            
            # Sample if requested
            if sample_size < len(job_pairs):
                import random
                job_pairs = random.sample(job_pairs, sample_size)
            
            print(f"🔮 Running predictions on {len(job_pairs):,} job transitions...")
            
            # Run predictions and collect data for analysis
            flagged_scenarios = {
                'management_demotions': [],
                'cross_function_jumps': [],
                'unrealistic_volume': [],
                'career_reversals': [],
                'suspicious_high_confidence': []
            }
            
            predictions_data = []
            
            for from_job, to_job in job_pairs:
                prediction = self.predict_pathway_feasibility(from_job['JobProfileID'], to_job['JobProfileID'])
                
                if prediction['prediction_status'] == 'success':
                    # Extract movement volume (assuming we convert to annual movements)
                    feasibility_pct = prediction.get('feasibility_percentage', 0)
                    annual_movements = feasibility_pct / 100 * 10  # Rough conversion for analysis
                    
                    # Debug: Print some sample values to understand the data
                    if len(predictions_data) < 5:  # First 5 predictions for debugging
                        print(f"DEBUG: {from_job['JobProfile'][:30]} → {to_job['JobProfile'][:30]}")
                        print(f"       Feasibility: {feasibility_pct:.2f}%, Annual Movements: {annual_movements:.2f}")
                        print(f"       Management: {from_job['ManagementLevel']} → {to_job['ManagementLevel']}")
                        print(f"       Function: {from_job['JobFunction']} → {to_job['JobFunction']}")
                        print()
                    
                    scenario = {
                        'from_job_id': from_job['JobProfileID'],
                        'to_job_id': to_job['JobProfileID'],
                        'from_job_title': from_job['JobProfile'],
                        'to_job_title': to_job['JobProfile'],
                        'from_function': from_job['JobFunction'],
                        'to_function': to_job['JobFunction'],
                        'from_management_level': from_job['ManagementLevel'],
                        'to_management_level': to_job['ManagementLevel'],
                        'from_category': from_job['JobCategory'],
                        'to_category': to_job['JobCategory'],
                        'predicted_annual_movements': annual_movements,
                        'confidence_score': prediction.get('confidence_score', 0),
                        'feasibility_percentage': feasibility_pct
                    }
                    
                    predictions_data.append(scenario)
                    
                    # Run sanity checks
                    self._check_management_progression(scenario, flagged_scenarios, check_categories)
                    self._check_function_transitions(scenario, flagged_scenarios, check_categories)
                    self._check_volume_realism(scenario, flagged_scenarios, check_categories, threshold)
                    self._check_career_logic(scenario, flagged_scenarios, check_categories)
            
            # Generate analysis report
            analysis_results = self._generate_sanity_report(flagged_scenarios, predictions_data, check_categories)
            
            # Add all predictions data for CSV export
            analysis_results['all_predictions'] = predictions_data
            analysis_results['sample_stats'] = {
                'min_annual_movements': min([p['predicted_annual_movements'] for p in predictions_data]) if predictions_data else 0,
                'max_annual_movements': max([p['predicted_annual_movements'] for p in predictions_data]) if predictions_data else 0,
                'avg_annual_movements': sum([p['predicted_annual_movements'] for p in predictions_data]) / len(predictions_data) if predictions_data else 0,
                'min_feasibility': min([p['feasibility_percentage'] for p in predictions_data]) if predictions_data else 0,
                'max_feasibility': max([p['feasibility_percentage'] for p in predictions_data]) if predictions_data else 0
            }
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"Sanity check analysis failed: {e}")
            return {'error': str(e)}
    
    def _check_management_progression(self, scenario: Dict, flagged_scenarios: Dict, categories: List[str]):
        """Check for unrealistic management level progressions."""
        if 'management_demotions' not in categories:
            return
            
        try:
            # Extract numeric levels (Group 1 = senior, Group 5 = junior)
            from_level = int(str(scenario['from_management_level']).replace('Group ', '').replace('Group', ''))
            to_level = int(str(scenario['to_management_level']).replace('Group ', '').replace('Group', ''))
            
            # Flag demotions with high predicted volume
            # Group 1 = Senior, Group 5 = Junior, so from_level < to_level = PROMOTION
            # We want to flag DEMOTIONS: from_level > to_level (e.g. Group 2 -> Group 4)
            if (from_level > to_level and  # Demotion (Group 2 -> Group 4)
                scenario['predicted_annual_movements'] > 0.05):  # Lower threshold for realistic detection
                
                flagged_scenarios['management_demotions'].append({
                    **scenario,
                    'flag_reason': f"Demotion from Group {from_level} to Group {to_level} with {scenario['predicted_annual_movements']:.1f} movements/year",
                    'severity': 'high' if scenario['predicted_annual_movements'] > 0.08 else 'medium'
                })
        except:
            pass  # Skip if management level parsing fails
    
    def _check_function_transitions(self, scenario: Dict, flagged_scenarios: Dict, categories: List[str]):
        """Check for unrealistic cross-functional transitions."""
        if 'cross_function_jumps' not in categories:
            return
            
        # Flag high-volume cross-function transitions (often unrealistic)
        if (scenario['from_function'] != scenario['to_function'] and
            scenario['predicted_annual_movements'] > 0.08):  # Adjusted for realistic data range
            
            flagged_scenarios['cross_function_jumps'].append({
                **scenario,
                'flag_reason': f"Cross-function jump {scenario['from_function']} → {scenario['to_function']} with {scenario['predicted_annual_movements']:.1f} movements/year",
                'severity': 'high' if scenario['predicted_annual_movements'] > 0.09 else 'medium'
            })
    
    def _check_volume_realism(self, scenario: Dict, flagged_scenarios: Dict, categories: List[str], threshold: float):
        """Check for unrealistically high movement volumes."""
        if 'unrealistic_volume' not in categories:
            return
            
        if scenario['predicted_annual_movements'] > threshold:
            flagged_scenarios['unrealistic_volume'].append({
                **scenario,
                'flag_reason': f"High movement volume: {scenario['predicted_annual_movements']:.1f} movements/year (threshold: {threshold})",
                'severity': 'critical' if scenario['predicted_annual_movements'] > threshold * 2 else 'high'
            })
    
    def _check_career_logic(self, scenario: Dict, flagged_scenarios: Dict, categories: List[str]):
        """Check for illogical career progressions."""
        if 'career_reversals' not in categories:
            return
            
        # Flag scenarios that seem backwards (e.g., specialist → generalist with high volume)
        suspicious_patterns = [
            ('Manager', 'Graduate'),
            ('Senior', 'Junior'),
            ('Lead', 'Trainee'),
            ('Director', 'Analyst')
        ]
        
        from_title = scenario['from_job_title'].lower()
        to_title = scenario['to_job_title'].lower()
        
        for senior_keyword, junior_keyword in suspicious_patterns:
            if (senior_keyword.lower() in from_title and 
                junior_keyword.lower() in to_title and
                scenario['predicted_annual_movements'] > 0.05):  # Adjusted threshold
                
                flagged_scenarios['career_reversals'].append({
                    **scenario,
                    'flag_reason': f"Potential career reversal: {scenario['from_job_title']} → {scenario['to_job_title']}",
                    'severity': 'medium'
                })
                break
    
    def _generate_sanity_report(self, flagged_scenarios: Dict, predictions_data: List[Dict], categories: List[str]) -> Dict:
        """Generate comprehensive sanity check report."""
        total_predictions = len(predictions_data)
        total_flagged = sum(len(flags) for flags in flagged_scenarios.values())
        
        print(f"🧠 PATHWAY SANITY CHECK RESULTS")
        print(f"{'='*80}")
        # Calculate and display value ranges
        if predictions_data:
            movements = [p['predicted_annual_movements'] for p in predictions_data]
            feasibility = [p['feasibility_percentage'] for p in predictions_data]
            confidence = [p['confidence_score'] for p in predictions_data]
            
            print(f"📊 SUMMARY:")
            print(f"   • Total Predictions Analyzed: {total_predictions:,}")
            print(f"   • Total Scenarios Flagged: {total_flagged:,} ({total_flagged/total_predictions*100:.1f}%)")
            print(f"\n📈 VALUE RANGES (Debug Info):")
            print(f"   • Annual Movements: {min(movements):.2f} - {max(movements):.2f} (avg: {sum(movements)/len(movements):.2f})")
            print(f"   • Feasibility %: {min(feasibility):.2f}% - {max(feasibility):.2f}% (avg: {sum(feasibility)/len(feasibility):.2f}%)")
            print(f"   • Confidence: {min(confidence):.3f} - {max(confidence):.3f} (avg: {sum(confidence)/len(confidence):.3f})")
        else:
            print(f"📊 SUMMARY:")
            print(f"   • Total Predictions Analyzed: {total_predictions:,}")
            print(f"   • Total Scenarios Flagged: {total_flagged:,} ({total_flagged/total_predictions*100:.1f}%)")
        
        for category in categories:
            if category in flagged_scenarios:
                count = len(flagged_scenarios[category])
                print(f"   • {category.replace('_', ' ').title()}: {count:,} flagged")
        
        print(f"\n🚨 DETAILED FLAGGED SCENARIOS:")
        
        for category in categories:
            if category in flagged_scenarios and flagged_scenarios[category]:
                print(f"\n📋 {category.replace('_', ' ').title()}:")
                
                # Sort by severity and show top issues
                flagged = sorted(flagged_scenarios[category], 
                               key=lambda x: {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}.get(x['severity'], 1), 
                               reverse=True)
                
                for i, scenario in enumerate(flagged[:10]):  # Show top 10 per category
                    severity_emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}.get(scenario['severity'], '⚪')
                    print(f"   {i+1:2d}. {severity_emoji} {scenario['flag_reason']}")
                    print(f"       {scenario['from_job_title']} → {scenario['to_job_title']}")
                    print(f"       Confidence: {scenario['confidence_score']:.1%}")
                
                if len(flagged) > 10:
                    print(f"       ... and {len(flagged)-10} more scenarios")
        
        print(f"\n💡 BUSINESS RECOMMENDATIONS:")
        
        # Generate recommendations based on findings
        recommendations = []
        
        if len(flagged_scenarios.get('management_demotions', [])) > total_predictions * 0.05:
            recommendations.append("• Review demotion predictions - high volumes may indicate model issues")
        
        if len(flagged_scenarios.get('cross_function_jumps', [])) > total_predictions * 0.1:
            recommendations.append("• Cross-function transitions show high volumes - validate against HR policies")
        
        if len(flagged_scenarios.get('unrealistic_volume', [])) > total_predictions * 0.02:
            recommendations.append("• Multiple high-volume predictions flagged - consider model recalibration")
        
        if not recommendations:
            recommendations.append("• Predictions appear realistic - no major concerns identified")
        
        for rec in recommendations:
            print(f"   {rec}")
        
        print(f"{'='*80}\n")
        
        return {
            'analysis_timestamp': datetime.now().isoformat(),
            'total_predictions': total_predictions,
            'total_flagged': total_flagged,
            'flagged_percentage': (total_flagged / total_predictions * 100) if total_predictions > 0 else 0,
            'flagged_scenarios': flagged_scenarios,
            'categories_analyzed': categories,
            'recommendations': recommendations
        }


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description='Pathway Predictor - Production ML Prediction Engine',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Predict specific job transition
    python pathway_predictor.py --job-to-job --from-job "12345" --to-job "67890"
    
    # Find top career paths from a job
    python pathway_predictor.py --job-to-many --from-job "12345" --top-n 10
    
    # Run full corpus analysis
    python pathway_predictor.py --corpus-analysis --sample-size 1000
        """
    )
    
    # Database and models
    parser.add_argument('--database', '-db', default='models/2025-Q3/business_context.sqlite',
                       help='Path to the production database')
    parser.add_argument('--models-dir', default='models/2025-Q3',
                       help='Directory containing trained ML models')
    
    # Prediction modes (mutually exclusive)
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument('--job-to-job', action='store_true',
                           help='Predict feasibility for specific job transition')
    mode_group.add_argument('--job-to-many', action='store_true', 
                           help='Predict feasibility from one job to many targets')
    mode_group.add_argument('--corpus-analysis', action='store_true',
                           help='Run full corpus analysis (all job pairs)')
    mode_group.add_argument('--sanity-check', action='store_true',
                           help='Run reality sanity checks on pathway predictions')
    
    # Job-to-job arguments
    parser.add_argument('--from-job', help='Source job profile ID')
    parser.add_argument('--to-job', help='Target job profile ID (for job-to-job mode)')
    
    # Job-to-many arguments
    parser.add_argument('--top-n', type=int, default=10,
                       help='Number of top predictions to return (job-to-many mode)')
    
    # Corpus analysis arguments
    parser.add_argument('--sample-size', type=int,
                       help='Sample size for corpus analysis (default: all pairs)')
    
    # Sanity check arguments
    parser.add_argument('--sanity-threshold', type=float, default=2.0,
                       help='Threshold for flagging unrealistic predictions (movements/year)')
    parser.add_argument('--check-categories', nargs='+', 
                       choices=['management_demotions', 'cross_function_jumps', 'unrealistic_volume', 'career_reversals'],
                       default=['management_demotions', 'cross_function_jumps', 'unrealistic_volume'],
                       help='Categories of sanity checks to perform')
    
    # Output options
    parser.add_argument('--output', '-o', help='Output file path for results')
    parser.add_argument('--format', choices=['json', 'csv'], default='json',
                       help='Output format')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.job_to_job or args.job_to_many:
        if not args.from_job:
            parser.error("--from-job is required for job-to-job and job-to-many modes")
    
    if args.job_to_job and not args.to_job:
        parser.error("--to-job is required for job-to-job mode")
    
    # Initialize predictor
    predictor = PathwayPredictor(args.database, args.models_dir)
    
    # Load trained models
    if not predictor.load_trained_models():
        print("❌ Failed to load trained models. Exiting.")
        return 1
    
    # Load and cache data for efficient predictions
    if not predictor.load_and_cache_data():
        print("❌ Failed to load and cache data. Exiting.")
        return 1
    
    # Run prediction based on mode
    results = None
    
    if args.job_to_job:
        results = predictor.predict_pathway_feasibility(args.from_job, args.to_job)
        
    elif args.job_to_many:
        results = predictor.predict_job_to_many(args.from_job, args.top_n)
        
    elif args.corpus_analysis:
        results = predictor.run_corpus_analysis(args.sample_size)
        
    elif args.sanity_check:
        results = predictor.run_sanity_checks(args.sample_size, args.sanity_threshold, args.check_categories)
    
    # Output results
    if results:
        if args.output:
            output_path = Path(args.output)
            if args.format == 'json':
                with open(output_path, 'w') as f:
                    json.dump(results, f, indent=2)
                print(f"💾 Results saved to {output_path}")
            elif args.format == 'csv':
                if args.sanity_check and 'all_predictions' in results:
                    # Export sanity check predictions data to CSV
                    df = pd.DataFrame(results['all_predictions'])
                    df.to_csv(output_path, index=False)
                    print(f"💾 Sanity check predictions data saved to {output_path}")
                elif isinstance(results, list):
                    pd.DataFrame(results).to_csv(output_path, index=False)
                    print(f"💾 Results saved to {output_path}")
                else:
                    print(f"⚠️  Cannot export to CSV - results format not supported")
        else:
            # Print to console (only for single predictions)
            if args.job_to_job:
                if args.format == 'json':
                    print(json.dumps(results, indent=2))
                else:
                    if isinstance(results, list):
                        df = pd.DataFrame(results)
                        print(df.to_string(index=False))
                    else:
                        print(json.dumps(results, indent=2))
            elif args.job_to_many:
                df = pd.DataFrame(results)
                print(df.to_string(index=False))
    
    return 0


if __name__ == '__main__':
    exit(main())