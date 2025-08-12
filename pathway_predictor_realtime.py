#!/usr/bin/env python3
"""
Real-Time Pathway Predictor - Production Web App Optimized
==========================================================

Self-contained, production-optimized ML prediction engine designed for real-time
web application integration with minimal memory footprint and fast single predictions.

Key Optimizations:
1. Self-contained - No external module dependencies
2. Hybrid caching - Only global context data (mobility scores, job hierarchy) 
3. Per-prediction queries - Fetch movement data only for specific job pairs
4. Low memory footprint - ~61KB vs ~15MB for batch processing
5. Real-time optimized - 2-5 predictions/sec with minimal latency

Architecture:
- Loads minimal global context once at startup (~715 mobility scores, job metadata)
- Queries database per-prediction for specific movement patterns
- Embeds essential feature engineering logic directly in the class
- Optimized for single/small batch predictions typical in web apps

Usage:
    predictor = RealtimePathwayPredictor()
    result = predictor.predict_pathway_feasibility("12345", "67890")
"""

import sqlite3
import pandas as pd
import numpy as np
import joblib
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import time
from datetime import datetime
import logging

# Progress bar (optional)
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RealtimePathwayPredictor:
    """
    Production-optimized pathway predictor for real-time web applications.
    
    Designed for minimal memory usage and fast single predictions by:
    1. Loading only essential global context data at startup
    2. Querying movement data per-prediction (not cached)
    3. Self-contained feature engineering (no external imports)
    """
    
    def __init__(self, db_path: Optional[str] = None, models_dir: str = "models/2025-Q3"):
        """
        Initialize the real-time pathway predictor.
        
        Args:
            db_path: Path to the production database
            models_dir: Directory containing trained ML models
        """
        if db_path is None:
            db_path = "models/2025-Q3/business_context.sqlite"
        
        self.db_path = Path(db_path)
        self.models_dir = Path(models_dir)
        
        # Storage for loaded models and metadata
        self.trained_models = {}
        self.feature_columns = []
        self.model_metadata = {}
        
        # Global context data (small memory footprint)
        self.source_mobility_scores = {}  # ~715 jobs -> ~10KB
        self.target_mobility_scores = {}  # ~715 jobs -> ~10KB  
        self.job_function_hierarchy = {}  # ~50 functions -> ~1KB
        self.jobs_metadata = {}          # ~715 jobs -> ~50KB
        # Total: ~71KB vs ~15MB for full caching
        
        print(f"🔮 RealtimePathwayPredictor initialized - DB: {self.db_path.name}")
    
    def load_trained_models(self) -> bool:
        """Load trained ML models and metadata."""
        try:
            # Load model metadata
            metadata_files = [
                self.models_dir / "model_metadata.json",
                Path("ml-training-metadata.json"),
                self.models_dir / "ml-training-metadata.json"
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
    
    def load_global_context(self) -> bool:
        """
        Load minimal global context data for efficient real-time predictions.
        
        This loads only the data that requires global statistics:
        1. Mobility scores (source & target) - requires aggregation across all jobs
        2. Job function hierarchy - requires all unique functions for consistent indexing
        3. Job metadata - for feature engineering
        """
        try:
            print("📊 Loading global context data...")
            
            with sqlite3.connect(self.db_path) as conn:
                # Load job metadata (needed for feature engineering)
                jobs_query = """
                SELECT JobProfileID, JobProfile, JobFunction, JobSubFunction, 
                       ManagementLevel, JobCategory
                FROM core_job_architecture
                ORDER BY JobProfile
                """
                jobs_df = pd.read_sql_query(jobs_query, conn)
                
                # Store as dictionary for fast lookup
                for _, job in jobs_df.iterrows():
                    self.jobs_metadata[job['JobProfileID']] = {
                        'JobProfile': job['JobProfile'],
                        'JobFunction': job['JobFunction'],
                        'JobSubFunction': job['JobSubFunction'],
                        'ManagementLevel': job['ManagementLevel'],
                        'JobCategory': job['JobCategory']
                    }
                
                # Create job function hierarchy (needed for distance calculation)
                job_functions = jobs_df['JobFunction'].unique()
                self.job_function_hierarchy = {func: idx for idx, func in enumerate(sorted(job_functions))}
                
                # Calculate mobility scores (requires global aggregation)
                print("📊 Calculating mobility scores...")
                self._calculate_mobility_scores(conn)
            
            print(f"✅ Loaded global context: {len(self.jobs_metadata):,} jobs, "
                  f"{len(self.source_mobility_scores):,} mobility scores, "
                  f"{len(self.job_function_hierarchy):,} job functions")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load global context: {e}")
            return False
    
    def _calculate_mobility_scores(self, conn: sqlite3.Connection) -> None:
        """
        Calculate mobility scores that require global context.
        
        This is the only operation that requires aggregating across all movement data,
        so we do it once at startup and cache the results.
        """
        # Load aggregated movement data for mobility calculation
        mobility_query = """
        SELECT 
            from_job_profile_id,
            to_job_profile_id,
            SUM(movement_count) as total_movement_count,
            SUM(unique_employees) as total_unique_employees,
            AVG(pct_total_movements) as avg_pct_total_movements
        FROM analytics_movement_patterns
        GROUP BY from_job_profile_id, to_job_profile_id
        """
        
        job_level_df = pd.read_sql_query(mobility_query, conn)
        
        # Calculate source mobility scores
        source_analysis = job_level_df.groupby('from_job_profile_id').agg({
            'to_job_profile_id': 'nunique',
            'total_movement_count': 'sum',
            'avg_pct_total_movements': 'mean'
        }).reset_index()
        
        for _, row in source_analysis.iterrows():
            job_id = row['from_job_profile_id']
            unique_destinations = row['to_job_profile_id']
            total_movements = row['total_movement_count']
            market_share = row['avg_pct_total_movements']
            
            # Calculate mobility score (same formula as training)
            diversity_score = min(unique_destinations / 10, 1.0)
            mobility_score = (
                diversity_score * 40 +
                min(unique_destinations / 10, 1) * 30 +
                min(total_movements / 100, 1) * 20 +
                min(market_share * 10, 1) * 10
            )
            
            self.source_mobility_scores[job_id] = mobility_score
        
        # Calculate target mobility scores  
        target_analysis = job_level_df.groupby('to_job_profile_id').agg({
            'from_job_profile_id': 'nunique',
            'total_movement_count': 'sum',
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
            
            self.target_mobility_scores[job_id] = mobility_score
    
    def _query_job_pair_movement_data(self, from_job_id: str, to_job_id: str) -> Dict[str, Any]:
        """
        Query movement data for a specific job pair.
        
        This is called per-prediction and only fetches data for the specific
        job transition being predicted, keeping memory usage minimal.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Query all monthly records for this job pair to calculate recency properly
                query = """
                SELECT 
                    movement_month,
                    movement_count,
                    unique_employees,
                    avg_days_between,
                    pct_total_movements
                FROM analytics_movement_patterns
                WHERE from_job_profile_id = ? AND to_job_profile_id = ?
                ORDER BY movement_month
                """
                
                monthly_results = conn.execute(query, (from_job_id, to_job_id)).fetchall()
                
                if monthly_results:  # Has movement data
                    # Calculate exact recency weighting using the same logic as MovementMLTrainer
                    recency_decay_rate = 0.4  # Same as config: movement_ml_training.yaml
                    
                    total_movements = 0
                    total_unique_employees = 0
                    avg_days_list = []
                    avg_pct_list = []
                    recency_weighted_activity = 0.0
                    movement_years = []
                    
                    # Get current year from data
                    all_years = [int(row[0][:4]) for row in monthly_results]  # Extract year from YYYY-MM
                    current_year = max(all_years)
                    
                    for row in monthly_results:
                        movement_month = row[0]
                        movement_count = row[1]
                        unique_employees = row[2]
                        avg_days = row[3]
                        pct_movements = row[4]
                        
                        # Extract year and calculate recency weight
                        movement_year = int(movement_month[:4])
                        years_ago = current_year - movement_year
                        recency_weight = recency_decay_rate ** years_ago
                        
                        # Accumulate values
                        total_movements += movement_count
                        total_unique_employees += unique_employees
                        if avg_days:
                            avg_days_list.append(avg_days)
                        if pct_movements:
                            avg_pct_list.append(pct_movements)
                        
                        # Calculate recency-weighted activity (key calculation!)
                        recency_weighted_activity += recency_weight
                        movement_years.append(movement_year)
                    
                    # Calculate temporal features exactly as in MovementMLTrainer
                    first_observed_year = min(movement_years)
                    last_observed_year = max(movement_years)
                    years_active = max(last_observed_year - first_observed_year + 1, 1)
                    transition_frequency = len(monthly_results)  # Number of distinct months
                    
                    # Calculate averages
                    avg_days = sum(avg_days_list) / len(avg_days_list) if avg_days_list else 365.0
                    avg_pct = sum(avg_pct_list) / len(avg_pct_list) if avg_pct_list else 0.0
                    
                    # Calculate exact recency_boost as in MovementMLTrainer
                    recency_boost = recency_weighted_activity / total_movements if total_movements > 0 else 1.0
                    
                    return {
                        'total_movement_count': total_movements,
                        'total_unique_employees': total_unique_employees,
                        'avg_days_between': avg_days,
                        'avg_pct_total_movements': avg_pct,
                        'transition_frequency': transition_frequency,
                        'years_active': years_active,
                        'avg_movements_per_year': total_movements / years_active,
                        'recency_weighted_activity': recency_weighted_activity,
                        'recency_boost': recency_boost
                    }
                else:
                    # No movement data - return zeros (unseen transition)
                    return {
                        'total_movement_count': 0,
                        'total_unique_employees': 0,
                        'avg_days_between': 365.0,
                        'avg_pct_total_movements': 0.0,
                        'transition_frequency': 0,
                        'years_active': 1,
                        'avg_movements_per_year': 0.0,
                        'recency_weighted_activity': 0.0,
                        'recency_boost': 1.0
                    }
                    
        except Exception as e:
            logger.error(f"Failed to query job pair movement data: {e}")
            # Return default values on error
            return {
                'total_movement_count': 0,
                'total_unique_employees': 0,
                'avg_days_between': 365.0,
                'avg_pct_total_movements': 0.0,
                'transition_frequency': 0,
                'years_active': 1,
                'avg_movements_per_year': 0.0,
                'recency_weighted_activity': 0.0,
                'recency_boost': 1.0
            }
    
    def _create_prediction_features(self, from_job_id: str, to_job_id: str) -> Optional[Dict[str, float]]:
        """
        Create ML features for a specific job transition.
        
        This combines:
        1. Per-prediction movement data (queried from DB)
        2. Global context data (cached at startup)
        3. Job architecture features (computed from metadata)
        """
        try:
            # Get job metadata
            from_job_info = self.jobs_metadata.get(from_job_id)
            to_job_info = self.jobs_metadata.get(to_job_id)
            
            if not from_job_info or not to_job_info:
                return None
            
            # Query movement data for this specific job pair
            movement_features = self._query_job_pair_movement_data(from_job_id, to_job_id)
            
            # Create complete feature set
            features = {
                # Movement features (from per-prediction query)
                **movement_features,
                
                # Mobility scores (from cached global context)
                'source_mobility_score': self.source_mobility_scores.get(from_job_id, 0.0),
                'target_mobility_score': self.target_mobility_scores.get(to_job_id, 0.0),
                
                # Job architecture features (computed from metadata)
                'same_job_function': float(from_job_info['JobFunction'] == to_job_info['JobFunction']),
                'same_job_sub_function': float(from_job_info['JobSubFunction'] == to_job_info['JobSubFunction']),
                'same_management_level': float(from_job_info['ManagementLevel'] == to_job_info['ManagementLevel']),
                'same_job_category': float(from_job_info['JobCategory'] == to_job_info['JobCategory']),
            }
            
            # Job function distance (using cached hierarchy)
            from_func_idx = self.job_function_hierarchy.get(from_job_info['JobFunction'], 0)
            to_func_idx = self.job_function_hierarchy.get(to_job_info['JobFunction'], 0)
            features['job_function_distance'] = float(abs(from_func_idx - to_func_idx))
            
            # Management level progression
            try:
                from_level = int(str(from_job_info['ManagementLevel']).replace('Group ', '').replace('Group', ''))
                to_level = int(str(to_job_info['ManagementLevel']).replace('Group ', '').replace('Group', ''))
                features['management_level_progression'] = float(to_level - from_level)
            except:
                features['management_level_progression'] = 0.0
            
            return features
            
        except Exception as e:
            logger.error(f"Failed to create prediction features: {e}")
            return None
    
    def predict_pathway_feasibility(self, from_job_id: str, to_job_id: str) -> Dict[str, Any]:
        """
        Predict pathway feasibility for a specific job transition.
        
        Optimized for real-time use:
        1. Uses cached global context data
        2. Queries only specific job pair movement data
        3. Fast feature engineering and prediction
        """
        try:
            # Create features using hybrid approach
            features = self._create_prediction_features(from_job_id, to_job_id)
            
            if features is None:
                return {
                    'from_job_id': from_job_id,
                    'to_job_id': to_job_id,
                    'feasibility_percentage': 0.0,
                    'confidence_score': 0.0,
                    'prediction_status': 'failed',
                    'error': 'Could not generate features'
                }
            
            # Prepare features for models (ensure correct order and missing values)
            feature_values = {}
            for col in self.feature_columns:
                feature_values[col] = features.get(col, 0.0)
            
            # Create DataFrame with proper column names to avoid sklearn warnings
            feature_df = pd.DataFrame([feature_values])
            
            # Get predictions from all models
            model_predictions = {}
            raw_predictions = []
            
            for model_name, model in self.trained_models.items():
                try:
                    raw_pred = model.predict(feature_df)[0]
                    model_predictions[model_name] = float(raw_pred)
                    raw_predictions.append(raw_pred)
                except Exception as e:
                    logger.warning(f"{model_name} prediction failed: {e}")
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
            
            # Convert to feasibility percentage
            max_movement = self.model_metadata.get('max_movement_volume', 100.0)
            feasibility_percentage = min(100.0, max(0.0, (ensemble_prediction / max_movement) * 100))
            
            # Calculate confidence from model agreement
            if len(raw_predictions) > 1:
                prediction_std = np.std(raw_predictions)
                prediction_mean = np.mean(raw_predictions)
                coefficient_of_variation = prediction_std / (prediction_mean + 1e-6)
                confidence_score = max(0.0, min(1.0, 1.0 - coefficient_of_variation))
            else:
                confidence_score = 0.5
            
            return {
                'from_job_id': from_job_id,
                'to_job_id': to_job_id,
                'feasibility_percentage': round(feasibility_percentage, 2),
                'confidence_score': round(confidence_score, 3),
                'prediction_status': 'success',
                'model_predictions': model_predictions,
                'ensemble_raw_prediction': float(ensemble_prediction),
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
        """Predict feasibility from one job to many potential targets."""
        try:
            # Get all possible target jobs
            target_jobs = list(self.jobs_metadata.keys())
            target_jobs = [job_id for job_id in target_jobs if job_id != from_job_id]
            
            print(f"🎯 Processing {len(target_jobs)} job transitions...")
            
            predictions = []
            
            if TQDM_AVAILABLE:
                target_jobs_iter = tqdm(target_jobs, desc="🎯 Job-to-many predictions", unit="jobs")
            else:
                target_jobs_iter = target_jobs
            
            for to_job_id in target_jobs_iter:
                result = self.predict_pathway_feasibility(from_job_id, to_job_id)
                
                # Add job metadata
                to_job_info = self.jobs_metadata.get(to_job_id, {})
                result.update({
                    'to_job_title': to_job_info.get('JobProfile', 'Unknown'),
                    'to_job_function': to_job_info.get('JobFunction', 'Unknown'),
                    'to_job_management_level': to_job_info.get('ManagementLevel', 'Unknown')
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
        """Run corpus analysis - optimized for memory efficiency."""
        try:
            # Get all job IDs
            job_ids = list(self.jobs_metadata.keys())
            
            # Generate job pairs
            job_pairs = []
            for from_job in job_ids:
                for to_job in job_ids:
                    if from_job != to_job:
                        job_pairs.append((from_job, to_job))
            
            total_pairs = len(job_pairs)
            
            # Sample if requested
            if sample_size and sample_size < total_pairs:
                import random
                job_pairs = random.sample(job_pairs, sample_size)
            
            print(f"🌐 Corpus Analysis: {len(job_ids)} jobs → {len(job_pairs):,} transitions")
            
            # Run predictions
            predictions = []
            start_time = time.time()
            
            if TQDM_AVAILABLE:
                job_pairs_iter = tqdm(job_pairs, desc="🔮 Predicting pathways", unit="predictions")
            else:
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
                'total_job_profiles': len(job_ids),
                'total_predictions': len(predictions),
                'successful_predictions': len(successful_predictions),
                'failed_predictions': len(predictions) - len(successful_predictions),
                'success_rate': len(successful_predictions) / len(predictions),
                'processing_time': time.time() - start_time,
                
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
                
                # Model info
                'model_info': {
                    'feature_columns_count': len(self.feature_columns),
                    'models_used': list(self.trained_models.keys()),
                    'training_metadata': self.model_metadata
                }
            }
            
            # Print results
            self._print_distribution_analysis(analysis_results)
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"Corpus analysis failed: {e}")
            return {'error': str(e)}
    
    def _print_distribution_analysis(self, results: Dict[str, Any]) -> None:
        """Print comprehensive distribution analysis."""
        print(f"\n{'='*80}")
        print(f"🎯 REAL-TIME PATHWAY PREDICTION ANALYSIS")
        print(f"{'='*80}")
        
        # Summary
        print(f"📊 SUMMARY:")
        print(f"   • Job Profiles: {results['total_job_profiles']:,}")
        print(f"   • Total Predictions: {results['total_predictions']:,}")
        print(f"   • Successful: {results['successful_predictions']:,} ({results['success_rate']*100:.1f}%)")
        print(f"   • Failed: {results['failed_predictions']:,}")
        print(f"   • Processing Time: {results['processing_time']:.1f} seconds")
        print(f"   • Rate: {results['total_predictions']/results['processing_time']:.1f} predictions/sec")
        
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
        
        # Memory optimization note
        print(f"\n⚡ REAL-TIME OPTIMIZATION:")
        print(f"   • Memory Footprint: ~71KB (vs ~15MB batch)")
        print(f"   • Per-prediction Queries: Movement data only")
        print(f"   • Cached Global Context: Mobility scores, job hierarchy")
        
        print(f"{'='*80}\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Real-Time Pathway Predictor - Production Web App Optimized',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Predict specific job transition
    python pathway_predictor_realtime.py --job-to-job --from-job "12345" --to-job "67890"
    
    # Find top career paths from a job  
    python pathway_predictor_realtime.py --job-to-many --from-job "12345" --top-n 10
    
    # Run corpus analysis (memory optimized)
    python pathway_predictor_realtime.py --corpus-analysis --sample-size 100
        """
    )
    
    # Database and models
    parser.add_argument('--database', '-db', default='models/2025-Q3/business_context.sqlite',
                       help='Path to the production database')
    parser.add_argument('--models-dir', default='models/2025-Q3',
                       help='Directory containing trained ML models')
    
    # Prediction modes
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument('--job-to-job', action='store_true',
                           help='Predict feasibility for specific job transition')
    mode_group.add_argument('--job-to-many', action='store_true',
                           help='Predict feasibility from one job to many targets')
    mode_group.add_argument('--corpus-analysis', action='store_true',
                           help='Run corpus analysis (memory optimized)')
    
    # Arguments
    parser.add_argument('--from-job', help='Source job profile ID')
    parser.add_argument('--to-job', help='Target job profile ID (for job-to-job mode)')
    parser.add_argument('--top-n', type=int, default=10,
                       help='Number of top predictions to return (job-to-many mode)')
    parser.add_argument('--sample-size', type=int,
                       help='Sample size for corpus analysis')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.job_to_job or args.job_to_many:
        if not args.from_job:
            parser.error("--from-job is required for job-to-job and job-to-many modes")
    
    if args.job_to_job and not args.to_job:
        parser.error("--to-job is required for job-to-job mode")
    
    # Initialize predictor
    predictor = RealtimePathwayPredictor(args.database, args.models_dir)
    
    # Load models and global context
    if not predictor.load_trained_models():
        print("❌ Failed to load trained models. Exiting.")
        return 1
    
    if not predictor.load_global_context():
        print("❌ Failed to load global context. Exiting.")
        return 1
    
    # Run prediction based on mode
    results = None
    
    if args.job_to_job:
        results = predictor.predict_pathway_feasibility(args.from_job, args.to_job)
        print(json.dumps(results, indent=2))
        
    elif args.job_to_many:
        results = predictor.predict_job_to_many(args.from_job, args.top_n)
        df = pd.DataFrame(results)
        print(df.to_string(index=False))
        
    elif args.corpus_analysis:
        results = predictor.run_corpus_analysis(args.sample_size)
    
    return 0


if __name__ == '__main__':
    exit(main())
