#!/usr/bin/env python3
"""
Test Script for Career Pathway Predictions

This script loads the trained ML models and predicts career transition
feasibility between job profiles using real-time inference.

Usage:
    # Interactive mode
    python test_pathway_predictions.py
    
    # List all available job profile IDs
    python test_pathway_predictions.py --list-jobs
    
    # Analyze specific job with top 5 similar jobs
    python test_pathway_predictions.py --job R0453.0 --top 5
    
    # Analyze specific job with top 10 similar jobs
    python test_pathway_predictions.py --job R0453.0 --top 10
    
    # Analyze specific job with custom target jobs
    python test_pathway_predictions.py --job R0453.0 --targets R0400.6,R0465.3,R0470.0
    
    # Performance test specific job (single prediction timing)
    python test_pathway_predictions.py --job R0453.0 --top 5 --perf-test
    
    # Batch performance test (cartesian product simulation)
    python test_pathway_predictions.py --perf-batch --sample-size 50 --batch-size 100
    
    # Run with production validation
    python test_pathway_predictions.py --job R0453.0 --top 5 --validate
    
    # Corpus-wide confidence analysis (production readiness check)
    python test_pathway_predictions.py --corpus-analysis --corpus-sample-size 100 --corpus-targets-per-job 50
    
    # Export corpus analysis results to CSV
    python test_pathway_predictions.py --corpus-analysis --corpus-export corpus_analysis_results.csv
"""

import sys
import os
import json
import sqlite3
import argparse
import time
import psutil
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import joblib

# Add src to path
src_path = os.path.join(os.path.dirname(__file__), 'src')
if os.path.exists(src_path) and src_path not in sys.path:
    sys.path.insert(0, src_path)

try:
    from skill_similarity_engine.models.versioning import ModelVersionManager
    # Note: We implement our own display formatting since JobDisplayManager expects 'jobs' table
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure to run this script from the skill-similarity-engine directory")
    sys.exit(1)


class PerformanceMonitor:
    """Monitor system performance during predictions."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.start_memory = None
        self.peak_memory = None
        self.cpu_samples = []
        self.monitoring = False
        self.monitor_thread = None
    
    def start_monitoring(self):
        """Start performance monitoring."""
        self.start_time = time.time()
        self.start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        self.peak_memory = self.start_memory
        self.cpu_samples = []
        self.monitoring = True
        
        # Start CPU monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_resources, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop performance monitoring and return results."""
        self.end_time = time.time()
        self.monitoring = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        return {
            'total_time': (self.end_time or 0) - (self.start_time or 0),
            'start_memory_mb': self.start_memory or 0,
            'end_memory_mb': end_memory,
            'peak_memory_mb': self.peak_memory or 0,
            'memory_increase_mb': (end_memory - (self.start_memory or 0)),
            'avg_cpu_percent': sum(self.cpu_samples) / len(self.cpu_samples) if self.cpu_samples else 0,
            'peak_cpu_percent': max(self.cpu_samples) if self.cpu_samples else 0
        }
    
    def _monitor_resources(self):
        """Monitor CPU and memory usage in background thread."""
        process = psutil.Process()
        while self.monitoring:
            try:
                # Sample CPU usage
                cpu_percent = process.cpu_percent()
                if cpu_percent > 0:  # Only record non-zero values
                    self.cpu_samples.append(cpu_percent)
                
                # Track peak memory
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                self.peak_memory = max(self.peak_memory, current_memory)
                
                time.sleep(0.1)  # Sample every 100ms
            except:
                break


class PathwayPredictor:
    """Real-time career pathway prediction using trained ML models."""
    
    def __init__(self):
        """Initialize the predictor with trained models."""
        self.models = {}
        self.feature_columns = []
        self.metadata = {}
        self.db_path = None
        
        # Load models and metadata
        self._load_models()
        
    def _load_models(self) -> None:
        """Load trained models from the quarterly folder."""
        # Get the current quarterly model directory
        version_manager = ModelVersionManager()
        current_quarter = version_manager.get_current_quarter()
        model_dir = version_manager.base_models_dir / current_quarter
        
        if not model_dir.exists():
            raise FileNotFoundError(f"No trained models found in {model_dir}. Please run ML training first.")
        
        print(f"📂 Loading models from: {model_dir}")
        
        # Load metadata
        metadata_path = model_dir / "model_metadata.json"
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                self.metadata = json.load(f)
            print(f"✅ Loaded model metadata (Best: {self.metadata.get('best_model', 'Unknown')})")
        
        # Load feature columns
        features_path = model_dir / "feature_columns.json"
        if features_path.exists():
            with open(features_path, 'r') as f:
                self.feature_columns = json.load(f)
            print(f"✅ Loaded {len(self.feature_columns)} feature columns")
        
        # Load all models
        model_files = {
            'Random Forest': 'random_forest_model.joblib',
            'Gradient Boosting': 'gradient_boosting_model.joblib', 
            'XGBoost': 'xgboost_model.joblib'
        }
        
        for model_name, filename in model_files.items():
            model_path = model_dir / filename
            if model_path.exists():
                self.models[model_name] = joblib.load(model_path)
                print(f"✅ Loaded {model_name} model")
        
        # Set database path
        self.db_path = model_dir / "business_context.sqlite"
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        
        # Note: JobDisplayManager expects 'jobs' table, but we have 'core_job_architecture'
        # We'll create our own display formatting method instead
        
        print(f"✅ Connected to database: {self.db_path}")
        print()
    
    def get_formatted_job_name(self, job_profile_id: str) -> str:
        """Get a nicely formatted job name using display logic."""
        try:
            query = """
            SELECT JobProfile, Job, ProfileTitleSuffix, ManagementLevel
            FROM core_job_architecture 
            WHERE JobProfileID = ?
            """
            
            with sqlite3.connect(str(self.db_path)) as conn:
                result = conn.execute(query, (job_profile_id,)).fetchone()
                
                if not result:
                    return job_profile_id
                
                job_profile, job, profile_title_suffix, management_level = result
                
                # Use Job (broader category) if available, otherwise JobProfile
                job_title = job if job else (job_profile.split(" - ")[0] if " - " in job_profile else job_profile)
                
                # Format as "Job Title - Suffix (Management Level)" for search-friendly display
                if profile_title_suffix and profile_title_suffix.strip():
                    return f"{job_title} - {profile_title_suffix} ({management_level})"
                else:
                    return f"{job_title} ({management_level})"
                    
        except Exception as e:
            print(f"⚠️  Error formatting job name for {job_profile_id}: {e}")
            return job_profile_id
    
    def get_job_profiles(self) -> pd.DataFrame:
        """Get available job profiles from the database."""
        query = """
        SELECT DISTINCT JobProfileID as job_profile_id, JobProfile as job_profile_name 
        FROM core_job_architecture 
        WHERE JobProfileID IS NOT NULL 
        ORDER BY JobProfile
        """
        
        with sqlite3.connect(str(self.db_path)) as conn:
            return pd.read_sql_query(query, conn)
    
    def get_most_similar_jobs(self, from_job_id: str, top_n: int = 5) -> List[str]:
        """Get the most similar jobs to the source job based on pre-computed similarities."""
        try:
            query = """
            SELECT job_to, similarity_score, enhanced_similarity_score
            FROM analytics_job_similarities
            WHERE job_from = ?
            AND job_to != job_from
            ORDER BY enhanced_similarity_score DESC
            LIMIT ?
            """
            
            with sqlite3.connect(str(self.db_path)) as conn:
                result = pd.read_sql_query(query, conn, params=(from_job_id, top_n))
                
                if result.empty:
                    print(f"⚠️  No similarity data found for {from_job_id}")
                    return []
                
                similar_jobs = result['job_to'].tolist()
                
                print(f"🔍 Found {len(similar_jobs)} most similar jobs to {from_job_id}:")
                for i, (_, row) in enumerate(result.iterrows(), 1):
                    job_name = self.get_formatted_job_name(row['job_to'])
                    print(f"  {i}. {row['job_to']}: {job_name}")
                    print(f"     Similarity: {row['enhanced_similarity_score']:.3f}")
                print()
                
                return similar_jobs
                
        except Exception as e:
            print(f"❌ Error getting similar jobs: {e}")
            return []
    
    def _generate_features(self, from_job_id: str, to_job_ids: List[str], quiet: bool = False) -> pd.DataFrame:
        """Generate ML features for pathway predictions."""
        if not quiet:
            print(f"🔧 Generating features for {from_job_id} → {to_job_ids}")
        
        # Get movement patterns for feature engineering
        query = """
        SELECT 
            from_job_profile_id,
            to_job_profile_id,
            movement_count as total_movement_count,
            unique_employees as total_unique_employees,
            avg_days_between,
            pct_total_movements as avg_pct_total_movements,
            1.0 as transition_frequency,
            1.0 as years_active,
            1.0 as avg_movements_per_year,
            1.0 as recency_boost
        FROM analytics_movement_patterns
        WHERE from_job_profile_id = ? AND to_job_profile_id IN ({})
        """.format(','.join(['?' for _ in to_job_ids]))
        
        params = tuple([from_job_id] + to_job_ids)
        
        with sqlite3.connect(str(self.db_path)) as conn:
            movement_df = pd.read_sql_query(query, conn, params=params)
        
        if movement_df.empty:
            if not quiet:
                print(f"⚠️  No historical movement patterns found for these pathways")
            # Create synthetic features for prediction
            movement_df = self._create_synthetic_features(from_job_id, to_job_ids)
        
        # Get job architecture features
        arch_features = self._get_job_architecture_features(from_job_id, to_job_ids)
        
        # Merge features
        feature_df = movement_df.merge(arch_features, on=['from_job_profile_id', 'to_job_profile_id'], how='left')
        
        # Ensure all required feature columns are present
        for col in self.feature_columns:
            if col not in feature_df.columns:
                feature_df[col] = 0  # Default value for missing features
        
        return feature_df[self.feature_columns]
    
    def _create_synthetic_features(self, from_job_id: str, to_job_ids: List[str]) -> pd.DataFrame:
        """Create synthetic features when no historical data exists."""
        rows = []
        for to_job_id in to_job_ids:
            rows.append({
                'from_job_profile_id': from_job_id,
                'to_job_profile_id': to_job_id,
                'total_movement_count': 0,
                'total_unique_employees': 0,
                'avg_days_between': 365.0,  # Default 1 year
                'avg_pct_total_movements': 0.0,
                'transition_frequency': 0.0,
                'years_active': 1.0,
                'avg_movements_per_year': 0.0,
                'recency_boost': 1.0
            })
        return pd.DataFrame(rows)
    
    def _get_job_architecture_features(self, from_job_id: str, to_job_ids: List[str]) -> pd.DataFrame:
        """Get job architecture-based features."""
        query = """
        SELECT 
            from_arch.JobProfileID as from_job_profile_id,
            to_arch.JobProfileID as to_job_profile_id,
            CASE WHEN from_arch.JobFunction = to_arch.JobFunction THEN 1 ELSE 0 END as same_job_function,
            CASE WHEN from_arch.JobSubFunction = to_arch.JobSubFunction THEN 1 ELSE 0 END as same_job_sub_function,
            CASE WHEN from_arch.ManagementLevel = to_arch.ManagementLevel THEN 1 ELSE 0 END as same_management_level,
            CASE WHEN from_arch.JobCategory = to_arch.JobCategory THEN 1 ELSE 0 END as same_job_category,
            ABS(CAST(SUBSTR(from_arch.ManagementLevel, -1) as INTEGER) - CAST(SUBSTR(to_arch.ManagementLevel, -1) as INTEGER)) as management_level_progression
        FROM core_job_architecture from_arch
        CROSS JOIN core_job_architecture to_arch
        WHERE from_arch.JobProfileID = ?
        AND to_arch.JobProfileID IN ({})
        """.format(','.join(['?' for _ in to_job_ids]))
        
        params = tuple([from_job_id] + to_job_ids)
        
        with sqlite3.connect(str(self.db_path)) as conn:
            arch_df = pd.read_sql_query(query, conn, params=params)
        
        # Add job function distance (simplified - could be enhanced with similarity scores)
        arch_df['job_function_distance'] = 1 - arch_df['same_job_function']  # 0 if same, 1 if different
        
        # Add mobility scores (simplified - could be enhanced with actual mobility data)
        arch_df['source_mobility_score'] = 0.5  # Default mobility
        arch_df['target_mobility_score'] = 0.5  # Default mobility
        
        return arch_df
    
    def predict_pathways(self, from_job_id: str, to_job_ids: List[str], quiet: bool = False) -> Dict[str, Any]:
        """Predict pathway feasibility for given job transitions."""
        if not self.models:
            raise RuntimeError("Models not loaded. Please run _load_models() first.")
        
        # Generate features
        features_df = self._generate_features(from_job_id, to_job_ids, quiet=quiet)
        
        if features_df.empty:
            return {
                'error': 'Could not generate features for prediction',
                'from_job_id': from_job_id,
                'to_job_ids': to_job_ids
            }
        
        # Make predictions with each model
        predictions = {}
        for model_name, model in self.models.items():
            try:
                pred = model.predict(features_df)
                predictions[model_name] = pred.tolist()
            except Exception as e:
                if not quiet:
                    print(f"⚠️  {model_name} prediction failed: {e}")
                predictions[model_name] = [0.0] * len(to_job_ids)
        
        # Calculate ensemble predictions and confidence
        results = []
        for i, to_job_id in enumerate(to_job_ids):
            pathway_predictions = [predictions[model][i] for model in predictions.keys()]
            
            # Ensemble prediction (mean)
            ensemble_pred = sum(pathway_predictions) / len(pathway_predictions)
            
            # Agreement calculation
            std_dev_value = pd.Series(pathway_predictions).std()
            if pd.isna(std_dev_value) or std_dev_value is None:
                std_dev_value = 0.0
            else:
                # Convert to float, handling potential Timedelta objects
                try:
                    std_dev_value = float(std_dev_value)
                except (TypeError, ValueError):
                    std_dev_value = 0.0
            
            agreement_rate = 1.0 - min(std_dev_value / max(ensemble_pred, 0.001), 1.0)  # Avoid division by zero
            
            # Confidence interval (simplified)
            z_score = self.metadata.get('ml_config', {}).get('z_score', 1.28)
            margin = z_score * std_dev_value
            
            results.append({
                'to_job_id': to_job_id,
                'predicted_movements': round(ensemble_pred, 4),
                'confidence_interval_lower': round(max(0, ensemble_pred - margin), 4),
                'confidence_interval_upper': round(ensemble_pred + margin, 4),
                'agreement_rate': round(agreement_rate, 3),
                'model_predictions': {
                    model: round(pred, 4) for model, pred in zip(predictions.keys(), pathway_predictions)
                }
            })
        
        return {
            'from_job_id': from_job_id,
            'predictions': results,
            'model_metadata': {
                'best_model': self.metadata.get('best_model'),
                'feature_count': len(self.feature_columns),
                'training_timestamp': self.metadata.get('training_timestamp')
            }
        }
    
    def performance_test_single(self, from_job_id: str, to_job_ids: List[str]) -> Dict[str, Any]:
        """Test performance for a single pathway prediction."""
        monitor = PerformanceMonitor()
        monitor.start_monitoring()
        
        # Time individual components
        feature_start = time.time()
        features_df = self._generate_features(from_job_id, to_job_ids)
        feature_time = time.time() - feature_start
        
        prediction_start = time.time()
        
        # Make predictions with each model
        predictions = {}
        model_times = {}
        for model_name, model in self.models.items():
            model_start = time.time()
            try:
                pred = model.predict(features_df)
                predictions[model_name] = pred.tolist()
                model_times[model_name] = time.time() - model_start
            except Exception as e:
                print(f"⚠️  {model_name} prediction failed: {e}")
                predictions[model_name] = [0.0] * len(to_job_ids)
                model_times[model_name] = 0.0
        
        prediction_time = time.time() - prediction_start
        
        # Calculate ensemble and results
        ensemble_start = time.time()
        results = []
        for i, to_job_id in enumerate(to_job_ids):
            pathway_predictions = [predictions[model][i] for model in predictions.keys()]
            ensemble_pred = sum(pathway_predictions) / len(pathway_predictions)
            
            std_dev_value = pd.Series(pathway_predictions).std()
            if pd.isna(std_dev_value) or std_dev_value is None:
                std_dev_value = 0.0
            else:
                try:
                    std_dev_value = float(std_dev_value)
                except (TypeError, ValueError):
                    std_dev_value = 0.0
            
            agreement_rate = 1.0 - min(std_dev_value / max(ensemble_pred, 0.001), 1.0)
            
            results.append({
                'to_job_id': to_job_id,
                'predicted_movements': round(ensemble_pred, 4),
                'agreement_rate': round(agreement_rate, 3)
            })
        
        ensemble_time = time.time() - ensemble_start
        
        # Stop monitoring
        perf_stats = monitor.stop_monitoring()
        
        return {
            'performance': {
                **perf_stats,
                'feature_generation_time': feature_time,
                'model_prediction_time': prediction_time,
                'ensemble_calculation_time': ensemble_time,
                'model_times': model_times,
                'predictions_per_second': len(to_job_ids) / perf_stats['total_time'],
                'pathways_tested': len(to_job_ids)
            },
            'predictions': results
        }
    
    def performance_test_batch(self, batch_size: int = 100, sample_jobs: Optional[List[str]] = None) -> Dict[str, Any]:
        """Test performance for batch predictions (simulating full cartesian product)."""
        print(f"🚀 Starting batch performance test (batch_size: {batch_size})")
        
        # Get job profiles for testing
        job_profiles = self.get_job_profiles()
        all_jobs = job_profiles['job_profile_id'].tolist()
        
        if sample_jobs:
            test_jobs = [job for job in sample_jobs if job in all_jobs]
        else:
            # Use a representative sample
            test_jobs = all_jobs[:min(50, len(all_jobs))]  # Limit to 50 for testing
        
        print(f"📊 Testing {len(test_jobs)} source jobs against {len(test_jobs)} target jobs")
        print(f"📈 Total pathway combinations: {len(test_jobs) * len(test_jobs):,}")
        
        # Performance tracking
        monitor = PerformanceMonitor()
        monitor.start_monitoring()
        
        total_predictions = 0
        successful_predictions = 0
        failed_predictions = 0
        batch_times = []
        
        start_time = time.time()
        
        for i, from_job in enumerate(test_jobs):
            batch_start = time.time()
            
            # Process in batches to avoid memory issues
            for batch_start_idx in range(0, len(test_jobs), batch_size):
                batch_end_idx = min(batch_start_idx + batch_size, len(test_jobs))
                to_jobs_batch = test_jobs[batch_start_idx:batch_end_idx]
                
                try:
                    # Generate features and predict
                    features_df = self._generate_features(from_job, to_jobs_batch)
                    
                    if not features_df.empty:
                        # Quick prediction without full ensemble calculation
                        best_model = self.models.get(self.metadata.get('best_model', 'XGBoost'))
                        if best_model:
                            pred = best_model.predict(features_df)
                            successful_predictions += len(to_jobs_batch)
                        else:
                            failed_predictions += len(to_jobs_batch)
                    else:
                        failed_predictions += len(to_jobs_batch)
                        
                    total_predictions += len(to_jobs_batch)
                    
                except Exception as e:
                    failed_predictions += len(to_jobs_batch)
                    total_predictions += len(to_jobs_batch)
            
            batch_time = time.time() - batch_start
            batch_times.append(batch_time)
            
            # Progress update
            if (i + 1) % 10 == 0 or i == 0:
                elapsed = time.time() - start_time
                rate = total_predictions / elapsed if elapsed > 0 else 0
                print(f"   Progress: {i+1:,}/{len(test_jobs):,} jobs processed, "
                      f"{total_predictions:,} predictions, {rate:.1f} pred/sec")
        
        # Final performance stats
        perf_stats = monitor.stop_monitoring()
        
        return {
            'performance': {
                **perf_stats,
                'total_predictions': total_predictions,
                'successful_predictions': successful_predictions,
                'failed_predictions': failed_predictions,
                'success_rate': successful_predictions / total_predictions if total_predictions > 0 else 0,
                'predictions_per_second': total_predictions / perf_stats['total_time'],
                'avg_batch_time': sum(batch_times) / len(batch_times) if batch_times else 0,
                'source_jobs_tested': len(test_jobs),
                'target_jobs_per_source': len(test_jobs),
                'batch_size': batch_size
            }
        }


class CorpusConfidenceAnalyzer:
    """Comprehensive corpus-wide confidence and business logic analysis."""
    
    def __init__(self, predictor: PathwayPredictor):
        """Initialize the corpus analyzer."""
        self.predictor = predictor
        self.db_path = predictor.db_path
        self.all_job_profiles = predictor.get_job_profiles()
        self.business_violations = []
        self.confidence_distribution = []
        self.management_level_violations = []
        self.cross_function_violations = []
        
    def analyze_corpus_confidence(self, sample_size: int = 100, targets_per_job: int = 50) -> Dict[str, Any]:
        """
        Analyze confidence distribution across the entire corpus.
        
        Args:
            sample_size: Number of source jobs to sample
            targets_per_job: Number of target jobs to analyze per source
            
        Returns:
            Comprehensive analysis results
        """
        print(f"🔍 Starting Corpus Confidence Analysis")
        print(f"📊 Sample: {sample_size} source jobs × {targets_per_job} targets = {sample_size * targets_per_job:,} predictions")
        print("=" * 80)
        
        # Sample jobs for analysis
        all_jobs = self.all_job_profiles['job_profile_id'].tolist()
        
        if sample_size >= len(all_jobs):
            source_jobs = all_jobs
        else:
            # Use systematic sampling for better representation
            step = len(all_jobs) // sample_size
            source_jobs = all_jobs[::step][:sample_size]
        
        print(f"📂 Analyzing {len(source_jobs)} source jobs from {len(all_jobs)} total jobs")
        
        # Performance monitoring
        monitor = PerformanceMonitor()
        monitor.start_monitoring()
        
        # Analysis storage
        all_predictions = []
        confidence_scores = []
        business_rule_violations = []
        management_violations = []
        cross_function_analysis = []
        
        # Progress tracking
        total_predictions = 0
        successful_predictions = 0
        
        start_time = time.time()
        
        for i, source_job in enumerate(source_jobs):
            # Simple progress indicator
            if i == 0 or (i + 1) % 25 == 0 or i == len(source_jobs) - 1:
                progress_pct = ((i + 1) / len(source_jobs)) * 100
                print(f"   Progress: {i+1:,}/{len(source_jobs):,} jobs ({progress_pct:.1f}%) - {total_predictions:,} predictions")
            
            try:
                # Get target jobs (mix of similar and random for comprehensive analysis)
                similar_targets = self._get_most_similar_jobs_quiet(source_job, min(targets_per_job // 2, 25))
                
                # Add random targets for broader coverage
                remaining_targets = targets_per_job - len(similar_targets)
                if remaining_targets > 0:
                    available_targets = [job for job in all_jobs if job != source_job and job not in similar_targets]
                    if len(available_targets) > remaining_targets:
                        import random
                        random_targets = random.sample(available_targets, remaining_targets)
                    else:
                        random_targets = available_targets
                    
                    target_jobs = similar_targets + random_targets
                else:
                    target_jobs = similar_targets
                
                # Make predictions (quiet mode to suppress detailed output)
                if target_jobs:
                    predictions = self.predictor.predict_pathways(source_job, target_jobs, quiet=True)
                    
                    if 'error' not in predictions:
                        # Process each prediction
                        for pred in predictions['predictions']:
                            total_predictions += 1
                            successful_predictions += 1
                            
                            # Store prediction data
                            prediction_data = {
                                'source_job': source_job,
                                'target_job': pred['to_job_id'],
                                'confidence': pred['agreement_rate'],
                                'predicted_movements': pred['predicted_movements'],
                                'model_predictions': pred['model_predictions']
                            }
                            all_predictions.append(prediction_data)
                            confidence_scores.append(pred['agreement_rate'])
                            
                            # Business rule analysis
                            violation = self._analyze_business_rules(source_job, pred['to_job_id'], pred['agreement_rate'])
                            if violation:
                                business_rule_violations.append(violation)
                            
                            # Management level analysis
                            mgmt_analysis = self._analyze_management_levels(source_job, pred['to_job_id'], pred['agreement_rate'])
                            management_violations.append(mgmt_analysis)
                            
                            # Cross-function analysis
                            func_analysis = self._analyze_function_changes(source_job, pred['to_job_id'], pred['agreement_rate'])
                            cross_function_analysis.append(func_analysis)
                    
            except Exception as e:
                # Silently continue on errors - we'll report summary stats
                continue
        
        # Final performance stats
        perf_stats = monitor.stop_monitoring()
        
        # Statistical analysis
        stats = self._calculate_confidence_statistics(confidence_scores)
        business_summary = self._summarize_business_violations(business_rule_violations)
        management_summary = self._summarize_management_violations(management_violations)
        function_summary = self._summarize_function_analysis(cross_function_analysis)
        
        # Compile results
        results = {
            'analysis_metadata': {
                'sample_size': len(source_jobs),
                'targets_per_job': targets_per_job,
                'total_predictions': total_predictions,
                'successful_predictions': successful_predictions,
                'analysis_time': perf_stats['total_time'],
                'predictions_per_second': total_predictions / perf_stats['total_time']
            },
            'confidence_distribution': stats,
            'business_rule_analysis': business_summary,
            'management_level_analysis': management_summary,
            'function_change_analysis': function_summary,
            'raw_predictions': all_predictions,
            'performance': perf_stats
        }
        
        return results
    
    def _get_most_similar_jobs_quiet(self, from_job_id: str, top_n: int = 5) -> List[str]:
        """Get the most similar jobs without printing detailed output."""
        try:
            query = """
            SELECT job_to, similarity_score, enhanced_similarity_score
            FROM analytics_job_similarities
            WHERE job_from = ?
            AND job_to != job_from
            ORDER BY enhanced_similarity_score DESC
            LIMIT ?
            """
            
            with sqlite3.connect(str(self.db_path)) as conn:
                result = pd.read_sql_query(query, conn, params=(from_job_id, top_n))
                
                if result.empty:
                    return []
                
                return result['job_to'].tolist()
                
        except Exception as e:
            return []
    
    def _analyze_business_rules(self, source_job: str, target_job: str, confidence: float) -> Optional[Dict[str, Any]]:
        """Analyze business rule violations for a prediction."""
        violations = []
        
        try:
            query = """
            SELECT 
                from_arch.JobProfileID as from_id,
                to_arch.JobProfileID as to_id,
                from_arch.ManagementLevel as from_level,
                to_arch.ManagementLevel as to_level,
                from_arch.JobFunction as from_function,
                to_arch.JobFunction as to_function,
                from_arch.JobProfile as from_title,
                to_arch.JobProfile as to_title
            FROM core_job_architecture from_arch
            JOIN core_job_architecture to_arch ON 1=1
            WHERE from_arch.JobProfileID = ? AND to_arch.JobProfileID = ?
            """
            
            with sqlite3.connect(str(self.db_path)) as conn:
                result = conn.execute(query, (source_job, target_job)).fetchone()
                
                if not result:
                    return None
                
                from_id, to_id, from_level, to_level, from_function, to_function, from_title, to_title = result
                
                # Same job violation
                if source_job == target_job and confidence > 0.2:
                    violations.append("same_job_high_confidence")
                
                # Management level violations
                try:
                    from_num = int(from_level.split()[-1]) if from_level else 0
                    to_num = int(to_level.split()[-1]) if to_level else 0
                    level_diff = from_num - to_num  # Positive = promotion, Negative = demotion
                    
                    # Major promotion with high confidence (suspicious)
                    if level_diff >= 3 and confidence > 0.8:
                        violations.append("major_promotion_high_confidence")
                    
                    # Any demotion with high confidence (rare in business)
                    if level_diff < -1 and confidence > 0.7:
                        violations.append("demotion_high_confidence")
                    
                    # Extreme demotion (almost never happens)
                    if level_diff < -2 and confidence > 0.5:
                        violations.append("extreme_demotion")
                        
                except (ValueError, AttributeError):
                    pass
                
                # Cross-function with extremely high confidence (rare)
                if from_function != to_function and confidence > 0.95:
                    violations.append("cross_function_extreme_confidence")
                
                if violations:
                    return {
                        'source_job': source_job,
                        'target_job': target_job,
                        'confidence': confidence,
                        'violations': violations,
                        'from_level': from_level,
                        'to_level': to_level,
                        'level_change': level_diff if 'level_diff' in locals() else None,
                        'from_function': from_function,
                        'to_function': to_function
                    }
                
        except Exception as e:
            print(f"⚠️  Business rule analysis failed for {source_job} → {target_job}: {e}")
        
        return None
    
    def _analyze_management_levels(self, source_job: str, target_job: str, confidence: float) -> Dict[str, Any]:
        """Detailed management level analysis."""
        violations = []
        analysis = {
            'source_job': source_job,
            'target_job': target_job,
            'confidence': confidence
        }
        
        try:
            query = """
            SELECT 
                from_arch.ManagementLevel as from_level,
                to_arch.ManagementLevel as to_level
            FROM core_job_architecture from_arch
            JOIN core_job_architecture to_arch ON 1=1
            WHERE from_arch.JobProfileID = ? AND to_arch.JobProfileID = ?
            """
            
            with sqlite3.connect(str(self.db_path)) as conn:
                result = conn.execute(query, (source_job, target_job)).fetchone()
                
                if result:
                    from_level, to_level = result
                    analysis.update({
                        'from_level': from_level,
                        'to_level': to_level
                    })
                    
                    try:
                        from_num = int(from_level.split()[-1]) if from_level else 0
                        to_num = int(to_level.split()[-1]) if to_level else 0
                        level_diff = from_num - to_num
                        
                        analysis['level_change'] = level_diff
                        analysis['movement_type'] = (
                            'promotion' if level_diff > 0 else
                            'demotion' if level_diff < 0 else
                            'lateral'
                        )
                        
                        # Identify specific violations
                        if level_diff < -2 and confidence > 0.3:
                            violations.append('extreme_demotion')
                        elif level_diff < -1 and confidence > 0.6:
                            violations.append('significant_demotion')
                        elif level_diff > 3 and confidence > 0.7:
                            violations.append('extreme_promotion')
                        
                        analysis['violations'] = violations
                        
                    except (ValueError, AttributeError):
                        analysis['level_change'] = None
                        analysis['movement_type'] = 'unknown'
        
        except Exception as e:
            analysis['error'] = str(e)
        
        return analysis
    
    def _analyze_function_changes(self, source_job: str, target_job: str, confidence: float) -> Dict[str, Any]:
        """Analyze job function change patterns."""
        analysis = {
            'source_job': source_job,
            'target_job': target_job,
            'confidence': confidence
        }
        
        try:
            query = """
            SELECT 
                from_arch.JobFunction as from_function,
                to_arch.JobFunction as to_function,
                from_arch.JobSubFunction as from_sub_function,
                to_arch.JobSubFunction as to_sub_function
            FROM core_job_architecture from_arch
            JOIN core_job_architecture to_arch ON 1=1
            WHERE from_arch.JobProfileID = ? AND to_arch.JobProfileID = ?
            """
            
            with sqlite3.connect(str(self.db_path)) as conn:
                result = conn.execute(query, (source_job, target_job)).fetchone()
                
                if result:
                    from_function, to_function, from_sub_function, to_sub_function = result
                    
                    analysis.update({
                        'from_function': from_function,
                        'to_function': to_function,
                        'same_function': from_function == to_function,
                        'same_sub_function': from_sub_function == to_sub_function
                    })
                    
                    if from_function == to_function:
                        analysis['change_type'] = 'within_function'
                        if from_sub_function != to_sub_function:
                            analysis['change_type'] = 'sub_function_change'
                    else:
                        analysis['change_type'] = 'cross_function'
                        
                        # Flag unusual cross-function high confidence
                        if confidence > 0.9:
                            analysis['flag'] = 'high_confidence_cross_function'
        
        except Exception as e:
            analysis['error'] = str(e)
        
        return analysis
    
    def _calculate_confidence_statistics(self, confidence_scores: List[float]) -> Dict[str, Any]:
        """Calculate comprehensive confidence distribution statistics."""
        if not confidence_scores:
            return {'error': 'No confidence scores to analyze'}
        
        import numpy as np
        
        scores = np.array(confidence_scores)
        
        # Basic statistics
        stats = {
            'count': len(scores),
            'mean': float(np.mean(scores)),
            'median': float(np.median(scores)),
            'std': float(np.std(scores)),
            'min': float(np.min(scores)),
            'max': float(np.max(scores)),
            'q25': float(np.percentile(scores, 25)),
            'q75': float(np.percentile(scores, 75))
        }
        
        # Distribution analysis
        stats['distribution'] = {
            'very_high_confidence': float(np.sum(scores > 0.95) / len(scores)),
            'high_confidence': float(np.sum((scores > 0.8) & (scores <= 0.95)) / len(scores)),
            'medium_confidence': float(np.sum((scores > 0.6) & (scores <= 0.8)) / len(scores)),
            'low_confidence': float(np.sum((scores > 0.3) & (scores <= 0.6)) / len(scores)),
            'very_low_confidence': float(np.sum(scores <= 0.3) / len(scores))
        }
        
        # Outlier detection
        iqr = stats['q75'] - stats['q25']
        lower_bound = stats['q25'] - 1.5 * iqr
        upper_bound = stats['q75'] + 1.5 * iqr
        
        stats['outliers'] = {
            'count': int(np.sum((scores < lower_bound) | (scores > upper_bound))),
            'percentage': float(np.sum((scores < lower_bound) | (scores > upper_bound)) / len(scores)),
            'high_outliers': int(np.sum(scores > upper_bound)),
            'low_outliers': int(np.sum(scores < lower_bound))
        }
        
        # Business concern thresholds
        stats['business_concerns'] = {
            'excessive_confidence': float(np.sum(scores > 0.98) / len(scores)),  # >98% confidence rare
            'unrealistic_precision': float(np.sum(scores > 0.99) / len(scores)),  # >99% almost impossible
            'low_differentiation': float(np.sum(scores > 0.9) / len(scores))      # >90% suggests poor differentiation
        }
        
        return stats
    
    def _summarize_business_violations(self, violations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize business rule violations."""
        if not violations:
            return {'total_violations': 0, 'violation_rate': 0.0}
        
        violation_types = {}
        for violation in violations:
            for vtype in violation['violations']:
                violation_types[vtype] = violation_types.get(vtype, 0) + 1
        
        most_common = None
        if violation_types:
            most_common = max(violation_types, key=lambda k: violation_types[k])
        
        return {
            'total_violations': len(violations),
            'violation_rate': len(violations) / len(self.confidence_distribution) if self.confidence_distribution else 0,
            'violation_types': violation_types,
            'most_common_violation': most_common
        }
    
    def _summarize_management_violations(self, violations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize management level analysis."""
        if not violations:
            return {'no_violations': True}
        
        movement_types = {}
        level_changes = []
        
        for analysis in violations:
            if 'movement_type' in analysis:
                mtype = analysis['movement_type']
                movement_types[mtype] = movement_types.get(mtype, 0) + 1
            
            if 'level_change' in analysis and analysis['level_change'] is not None:
                level_changes.append(analysis['level_change'])
        
        return {
            'total_analyzed': len(violations),
            'movement_types': movement_types,
            'avg_level_change': sum(level_changes) / len(level_changes) if level_changes else 0,
            'extreme_changes': len([lc for lc in level_changes if abs(lc) > 2])
        }
    
    def _summarize_function_analysis(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize function change analysis."""
        if not analyses:
            return {'no_data': True}
        
        change_types = {}
        high_confidence_cross_function = 0
        
        for analysis in analyses:
            if 'change_type' in analysis:
                ctype = analysis['change_type']
                change_types[ctype] = change_types.get(ctype, 0) + 1
            
            if analysis.get('flag') == 'high_confidence_cross_function':
                high_confidence_cross_function += 1
        
        return {
            'total_analyzed': len(analyses),
            'change_types': change_types,
            'suspicious_cross_function_moves': high_confidence_cross_function,
            'cross_function_rate': change_types.get('cross_function', 0) / len(analyses)
        }


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Test career pathway predictions using trained ML models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python test_pathway_predictions.py
  
  # Analyze specific job with top 5 similar jobs
  python test_pathway_predictions.py --job R0453.0 --top 5
  
  # Analyze specific job with custom target jobs
  python test_pathway_predictions.py --job R0453.0 --targets R0400.6,R0465.3
        """
    )
    
    parser.add_argument(
        '--job', '-j',
        type=str,
        help='Source job profile ID to analyze (e.g., R0453.0)'
    )
    
    parser.add_argument(
        '--top', '-t',
        type=int,
        default=5,
        help='Number of most similar jobs to analyze (default: 5)'
    )
    
    parser.add_argument(
        '--targets',
        type=str,
        help='Comma-separated list of target job profile IDs (overrides --top)'
    )
    
    parser.add_argument(
        '--list-jobs', '-l',
        action='store_true',
        help='List available job profile IDs and exit'
    )
    
    parser.add_argument(
        '--perf-test',
        action='store_true',
        help='Run performance test on the specified job and targets'
    )
    
    parser.add_argument(
        '--perf-batch',
        action='store_true',
        help='Run batch performance test (cartesian product simulation)'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Batch size for batch performance test (default: 100)'
    )
    
    parser.add_argument(
        '--sample-size',
        type=int,
        default=50,
        help='Number of jobs to sample for batch test (default: 50)'
    )
    
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Run production validation on predictions'
    )
    
    parser.add_argument(
        '--corpus-analysis',
        action='store_true',
        help='Run comprehensive corpus-wide confidence analysis'
    )
    
    parser.add_argument(
        '--corpus-sample-size',
        type=int,
        default=100,
        help='Number of source jobs to sample for corpus analysis (default: 100)'
    )
    
    parser.add_argument(
        '--corpus-targets-per-job',
        type=int,
        default=50,
        help='Number of target jobs to analyze per source job (default: 50)'
    )
    
    parser.add_argument(
        '--corpus-export',
        type=str,
        help='Export corpus analysis results to CSV file (provide filename)'
    )
    
    return parser.parse_args()


def main():
    """Main function to test pathway predictions."""
    args = parse_arguments()
    
    print("🚀 Career Pathway Prediction Test")
    print("=" * 50)
    
    try:
        # Initialize predictor
        predictor = PathwayPredictor()
        
        # Get available job profiles
        job_profiles = predictor.get_job_profiles()
        print(f"📊 Available Job Profiles: {len(job_profiles)}")
        print()
        
        # If list-jobs flag is set, show all jobs and exit
        if args.list_jobs:
            print("All Available Job Profiles:")
            for _, row in job_profiles.iterrows():
                job_id = row['job_profile_id']
                formatted_name = predictor.get_formatted_job_name(job_id)
                print(f"  {job_id}: {formatted_name}")
            return
        
        # Handle corpus analysis
        if args.corpus_analysis:
            print("🔍 Running Comprehensive Corpus Confidence Analysis")
            print("=" * 70)
            
            analyzer = CorpusConfidenceAnalyzer(predictor)
            results = analyzer.analyze_corpus_confidence(
                sample_size=args.corpus_sample_size,
                targets_per_job=args.corpus_targets_per_job
            )
            
            display_corpus_analysis_results(results)
            
            # Export results if requested
            if args.corpus_export:
                export_corpus_results(results, args.corpus_export)
            
            return
        
        # Handle batch performance test
        if args.perf_batch:
            print("🔥 Running Batch Performance Test (Cartesian Product Simulation)")
            print("=" * 70)
            
            job_profiles_list = job_profiles['job_profile_id'].tolist()
            sample_jobs = job_profiles_list[:args.sample_size]
            
            results = predictor.performance_test_batch(
                batch_size=args.batch_size,
                sample_jobs=sample_jobs
            )
            
            display_batch_performance_results(results)
            return
        
        # If job is specified via command line, use it
        if args.job:
            from_job = args.job
            
            # Validate source job
            if from_job not in job_profiles['job_profile_id'].values:
                print(f"❌ Job profile '{from_job}' not found.")
                print("Use --list-jobs to see available job profile IDs.")
                return
            
            # Get target jobs
            if args.targets:
                # Use custom targets
                to_jobs = [job.strip() for job in args.targets.split(',')]
                
                # Validate target jobs
                invalid_jobs = [job for job in to_jobs if job not in job_profiles['job_profile_id'].values]
                if invalid_jobs:
                    print(f"❌ Invalid job profile(s): {invalid_jobs}")
                    return
                    
                print(f"🎯 Analyzing custom pathway targets for {from_job}")
            else:
                # Use most similar jobs
                to_jobs = predictor.get_most_similar_jobs(from_job, args.top)
                if not to_jobs:
                    return
                    
                print(f"🎯 Analyzing top {len(to_jobs)} similar pathways for {from_job}")
            
            # Run performance test or normal prediction
            print()
            if args.perf_test:
                print("⚡ Running Performance Test")
                print("=" * 30)
                results = predictor.performance_test_single(from_job, to_jobs)
                display_single_performance_results(predictor, from_job, results)
            else:
                results = predictor.predict_pathways(from_job, to_jobs)
                
                if 'error' in results:
                    print(f"❌ Prediction failed: {results['error']}")
                    return
                
                # Run validation if requested
                if args.validate:
                    print("🔍 Running Production Validation...")
                    run_validation_check(predictor.db_path, from_job, results['predictions'])
                    print()
                
                # Display results
                display_prediction_results(predictor, from_job, results)
            
        else:
            # Interactive mode
            run_interactive_mode(predictor, job_profiles)
            
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


def display_prediction_results(predictor, from_job: str, results: Dict[str, Any]):
    """Display prediction results with focus on feasibility score."""
    print("📈 Career Pathway Feasibility Analysis:")
    print("=" * 60)
    
    # Get formatted name for source
    from_name = predictor.get_formatted_job_name(from_job)
    print(f"🏢 Source Job: {from_job}")
    print(f"   {from_name}")
    print()
    
    for i, pred in enumerate(results['predictions'], 1):
        to_job = pred['to_job_id']
        to_name = predictor.get_formatted_job_name(to_job)
        
        # Calculate feasibility score and grade
        feasibility_score = pred['agreement_rate']
        feasibility_percent = feasibility_score * 100
        
        # Determine feasibility grade and emoji
        if feasibility_score >= 0.95:
            grade = "A+"
            emoji = "🟢"
            label = "HIGHLY FEASIBLE"
            stars = "⭐⭐⭐⭐⭐"
        elif feasibility_score >= 0.90:
            grade = "A"
            emoji = "🟢"
            label = "VERY FEASIBLE"
            stars = "⭐⭐⭐⭐"
        elif feasibility_score >= 0.80:
            grade = "B+"
            emoji = "🟡"
            label = "FEASIBLE"
            stars = "⭐⭐⭐"
        elif feasibility_score >= 0.70:
            grade = "B"
            emoji = "🟠"
            label = "MODERATELY FEASIBLE"
            stars = "⭐⭐"
        else:
            grade = "C"
            emoji = "🔴"
            label = "LOW FEASIBILITY"
            stars = "⭐"
        
        # Format movement prediction
        movements = pred['predicted_movements']
        if movements >= 2.0:
            movement_desc = f"~{int(round(movements))} people per year"
        elif movements >= 1.0:
            movement_desc = "~1 person per year"
        elif movements >= 0.5:
            movement_desc = "~1 person every 2 years"
        elif movements >= 0.25:
            movement_desc = "~1 person every 4 years"
        else:
            movement_desc = "Very rare transition"
        
        print(f"🎯 Pathway {i}: {from_job} → {to_job}")
        print(f"   Target: {to_name}")
        print()
        print(f"   {emoji} FEASIBILITY SCORE: {feasibility_percent:.1f}% (Grade {grade})")
        print(f"   {stars} {label}")
        print()
        print(f"   📊 Supporting Evidence:")
        print(f"   • Expected Transitions: {movement_desc}")
        print(f"   • Model Confidence: {feasibility_percent:.1f}% agreement")
        print(f"   • Prediction Range: {pred['confidence_interval_lower']:.2f} - {pred['confidence_interval_upper']:.2f} movements/year")
        print()
        print(f"   🤖 Model Details:")
        for model, prediction in pred['model_predictions'].items():
            print(f"     • {model}: {prediction:.3f}")
        print()
        print("-" * 60)
    
    # Feasibility Summary
    print("🏆 Feasibility Summary:")
    sorted_predictions = sorted(results['predictions'], key=lambda x: x['agreement_rate'], reverse=True)
    
    highly_feasible = [p for p in sorted_predictions if p['agreement_rate'] >= 0.95]
    very_feasible = [p for p in sorted_predictions if 0.90 <= p['agreement_rate'] < 0.95]
    feasible = [p for p in sorted_predictions if 0.80 <= p['agreement_rate'] < 0.90]
    
    print(f"   🟢 Highly Feasible (95%+): {len(highly_feasible)} pathways")
    print(f"   🟢 Very Feasible (90-94%): {len(very_feasible)} pathways")
    print(f"   🟡 Feasible (80-89%): {len(feasible)} pathways")
    print(f"   🟠 Lower Feasibility (<80%): {len(sorted_predictions) - len(highly_feasible) - len(very_feasible) - len(feasible)} pathways")
    
    if highly_feasible:
        best_pathway = highly_feasible[0]
        best_name = predictor.get_formatted_job_name(best_pathway['to_job_id'])
        print(f"   ⭐ Top Recommendation: {best_pathway['to_job_id']} ({best_pathway['agreement_rate']*100:.1f}%)")
        print(f"     {best_name}")
    print()
    
    print("📊 Analysis Metadata:")
    metadata = results['model_metadata']
    print(f"   ML Engine: {metadata['best_model']} (primary)")
    print(f"   Features Analyzed: {metadata['feature_count']}")
    print(f"   Model Training: {metadata['training_timestamp']}")
    print(f"   Ensemble Models: 3 (Random Forest, Gradient Boosting, XGBoost)")


def display_single_performance_results(predictor, from_job: str, results: Dict[str, Any]):
    """Display performance results for a single prediction test."""
    perf = results['performance']
    predictions = results['predictions']
    
    # Get formatted name for source
    from_name = predictor.get_formatted_job_name(from_job)
    
    print(f"🏢 Source Job: {from_job}")
    print(f"   {from_name}")
    print()
    
    # Performance Summary
    print("⚡ Performance Summary:")
    print(f"   Total Time: {perf['total_time']:.3f}s")
    print(f"   Predictions/Second: {perf['predictions_per_second']:.1f}")
    print(f"   Pathways Tested: {perf['pathways_tested']}")
    
    # Check 3-second target
    target_met = "✅" if perf['total_time'] <= 3.0 else "❌"
    print(f"   3-Second Target: {target_met} ({perf['total_time']:.3f}s)")
    print()
    
    # Detailed Timing
    print("⏱️  Detailed Timing:")
    print(f"   Feature Generation: {perf['feature_generation_time']:.3f}s ({perf['feature_generation_time']/perf['total_time']*100:.1f}%)")
    print(f"   Model Predictions: {perf['model_prediction_time']:.3f}s ({perf['model_prediction_time']/perf['total_time']*100:.1f}%)")
    print(f"   Ensemble Calculation: {perf['ensemble_calculation_time']:.3f}s ({perf['ensemble_calculation_time']/perf['total_time']*100:.1f}%)")
    print()
    
    # Model Performance
    print("🤖 Individual Model Times:")
    for model, time_taken in perf['model_times'].items():
        print(f"   {model}: {time_taken:.3f}s")
    print()
    
    # Resource Usage
    print("💾 Resource Usage:")
    print(f"   Memory Start: {perf['start_memory_mb']:.1f} MB")
    print(f"   Memory Peak: {perf['peak_memory_mb']:.1f} MB")
    print(f"   Memory Increase: {perf['memory_increase_mb']:.1f} MB")
    print(f"   CPU Average: {perf['avg_cpu_percent']:.1f}%")
    print(f"   CPU Peak: {perf['peak_cpu_percent']:.1f}%")
    print()
    
    # Sample Predictions with Feasibility Scores
    print("📈 Sample Feasibility Scores:")
    for i, pred in enumerate(predictions[:3]):  # Show first 3
        to_name = predictor.get_formatted_job_name(pred['to_job_id'])
        feasibility_percent = pred['agreement_rate'] * 100
        
        # Quick grade
        if pred['agreement_rate'] >= 0.95:
            grade_emoji = "🟢 A+"
        elif pred['agreement_rate'] >= 0.90:
            grade_emoji = "🟢 A"
        elif pred['agreement_rate'] >= 0.80:
            grade_emoji = "🟡 B+"
        elif pred['agreement_rate'] >= 0.70:
            grade_emoji = "🟠 B"
        else:
            grade_emoji = "🔴 C"
            
        print(f"   {i+1}. {pred['to_job_id']}: {to_name}")
        print(f"      Feasibility: {feasibility_percent:.1f}% {grade_emoji}")
        print(f"      Expected: ~{pred['predicted_movements']:.1f} movements/year")


def display_batch_performance_results(results: Dict[str, Any]):
    """Display performance results for batch testing."""
    perf = results['performance']
    
    print("🔥 Batch Performance Test Results")
    print("=" * 50)
    
    # Overall Performance
    print("📊 Overall Performance:")
    print(f"   Total Time: {perf['total_time']:.1f}s ({perf['total_time']/60:.1f} minutes)")
    print(f"   Total Predictions: {perf['total_predictions']:,}")
    print(f"   Successful: {perf['successful_predictions']:,} ({perf['success_rate']*100:.1f}%)")
    print(f"   Failed: {perf['failed_predictions']:,}")
    print(f"   Predictions/Second: {perf['predictions_per_second']:.1f}")
    print()
    
    # Throughput Analysis
    print("⚡ Throughput Analysis:")
    print(f"   Source Jobs Tested: {perf['source_jobs_tested']}")
    print(f"   Target Jobs per Source: {perf['target_jobs_per_source']}")
    print(f"   Batch Size: {perf['batch_size']}")
    print(f"   Average Batch Time: {perf['avg_batch_time']:.3f}s")
    print()
    
    # Scalability Estimates
    total_jobs = 715  # From schema
    full_cartesian = total_jobs * total_jobs
    estimated_time = full_cartesian / perf['predictions_per_second']
    
    print("🚀 Production Scalability Estimates:")
    print(f"   Full Cartesian Product: {full_cartesian:,} predictions")
    print(f"   Estimated Time for Full Dataset: {estimated_time:.1f}s ({estimated_time/60:.1f} minutes)")
    print(f"   Memory Usage: {perf['peak_memory_mb']:.1f} MB peak")
    print()
    
    # Web App Performance Assessment
    single_request_time = 1.0 / perf['predictions_per_second']
    print("🌐 Web Application Performance Assessment:")
    print(f"   Single Pathway Prediction: {single_request_time:.3f}s")
    
    if single_request_time <= 0.5:
        assessment = "🟢 EXCELLENT - Sub-500ms response time"
    elif single_request_time <= 1.0:
        assessment = "🟡 GOOD - Sub-1s response time"
    elif single_request_time <= 3.0:
        assessment = "🟠 ACCEPTABLE - Sub-3s response time"
    else:
        assessment = "🔴 POOR - Over 3s response time"
    
    print(f"   Assessment: {assessment}")
    print()
    
    # Resource Usage
    print("💾 Resource Usage:")
    print(f"   Memory Start: {perf['start_memory_mb']:.1f} MB")
    print(f"   Memory Peak: {perf['peak_memory_mb']:.1f} MB")
    print(f"   Memory Increase: {perf['memory_increase_mb']:.1f} MB")
    print(f"   CPU Average: {perf['avg_cpu_percent']:.1f}%")
    print(f"   CPU Peak: {perf['peak_cpu_percent']:.1f}%")


def display_corpus_analysis_results(results: Dict[str, Any]):
    """Display comprehensive corpus analysis results."""
    metadata = results['analysis_metadata']
    confidence_dist = results['confidence_distribution']
    business_analysis = results['business_rule_analysis']
    management_analysis = results['management_level_analysis']
    function_analysis = results['function_change_analysis']
    
    print("\n🎯 CORPUS CONFIDENCE ANALYSIS RESULTS")
    print("=" * 80)
    
    # Analysis Overview
    print("📊 ANALYSIS OVERVIEW:")
    print(f"   Total Predictions Analyzed: {metadata['total_predictions']:,}")
    print(f"   Sample Size: {metadata['sample_size']} source jobs")
    print(f"   Targets per Job: {metadata.get('targets_per_job', 'Variable')}")
    print(f"   Analysis Time: {metadata['analysis_time']:.1f}s")
    print(f"   Processing Rate: {metadata['predictions_per_second']:.1f} predictions/sec")
    print()
    
    # Confidence Distribution Analysis
    print("📈 CONFIDENCE DISTRIBUTION ANALYSIS:")
    print("=" * 50)
    
    dist = confidence_dist['distribution']
    print(f"   Mean Confidence: {confidence_dist['mean']:.3f} ({confidence_dist['mean']*100:.1f}%)")
    print(f"   Median Confidence: {confidence_dist['median']:.3f} ({confidence_dist['median']*100:.1f}%)")
    print(f"   Standard Deviation: {confidence_dist['std']:.3f}")
    print(f"   Range: {confidence_dist['min']:.3f} - {confidence_dist['max']:.3f}")
    print()
    
    print("   📊 Distribution Breakdown:")
    print(f"   🔴 Very High (>95%): {dist['very_high_confidence']*100:.1f}% of predictions")
    print(f"   🟠 High (80-95%): {dist['high_confidence']*100:.1f}% of predictions")
    print(f"   🟡 Medium (60-80%): {dist['medium_confidence']*100:.1f}% of predictions")
    print(f"   🟢 Low (30-60%): {dist['low_confidence']*100:.1f}% of predictions")
    print(f"   🔵 Very Low (≤30%): {dist['very_low_confidence']*100:.1f}% of predictions")
    print()
    
    # Business Concerns Section
    concerns = confidence_dist['business_concerns']
    print("🚨 BUSINESS CONCERN INDICATORS:")
    print("=" * 40)
    
    # Assess overall health
    total_concerns = (concerns['excessive_confidence'] + 
                     concerns['unrealistic_precision'] + 
                     concerns['low_differentiation'])
    
    if concerns['unrealistic_precision'] > 0.05:  # >5% at 99%+
        concern_level = "🔴 CRITICAL"
        recommendation = "IMMEDIATE MODEL REVIEW REQUIRED"
    elif concerns['excessive_confidence'] > 0.15:  # >15% at 98%+
        concern_level = "🟠 HIGH"
        recommendation = "Model calibration recommended"
    elif concerns['low_differentiation'] > 0.4:   # >40% at 90%+
        concern_level = "🟡 MODERATE"
        recommendation = "Monitor model discrimination"
    else:
        concern_level = "🟢 LOW"
        recommendation = "Model confidence appears reasonable"
    
    print(f"   Overall Assessment: {concern_level}")
    print(f"   Recommendation: {recommendation}")
    print()
    print(f"   Excessive Confidence (>98%): {concerns['excessive_confidence']*100:.1f}%")
    print(f"   Unrealistic Precision (>99%): {concerns['unrealistic_precision']*100:.1f}%")
    print(f"   Low Differentiation (>90%): {concerns['low_differentiation']*100:.1f}%")
    print()
    
    # Business Rule Violations
    print("⚖️  BUSINESS RULE VIOLATIONS:")
    print("=" * 35)
    
    if business_analysis['total_violations'] == 0:
        print("   ✅ No business rule violations detected")
    else:
        violation_rate = business_analysis['violation_rate'] * 100
        print(f"   Total Violations: {business_analysis['total_violations']:,}")
        print(f"   Violation Rate: {violation_rate:.2f}%")
        
        if violation_rate > 10:
            print("   🔴 HIGH VIOLATION RATE - Model needs review")
        elif violation_rate > 5:
            print("   🟡 MODERATE VIOLATION RATE - Monitor closely")
        else:
            print("   🟢 LOW VIOLATION RATE - Acceptable performance")
        
        if 'violation_types' in business_analysis:
            print("\n   Violation Breakdown:")
            for vtype, count in business_analysis['violation_types'].items():
                percentage = (count / metadata['total_predictions']) * 100
                print(f"   • {vtype.replace('_', ' ').title()}: {count:,} ({percentage:.2f}%)")
    print()
    
    # Management Level Analysis
    print("👔 MANAGEMENT LEVEL ANALYSIS:")
    print("=" * 35)
    
    if management_analysis.get('no_violations', False):
        print("   ✅ No management level issues detected")
    else:
        print(f"   Total Pathways Analyzed: {management_analysis.get('total_analyzed', 0):,}")
        
        if 'movement_types' in management_analysis:
            print("\n   Movement Type Distribution:")
            for mtype, count in management_analysis['movement_types'].items():
                print(f"   • {mtype.title()}: {count:,}")
        
        if management_analysis.get('extreme_changes', 0) > 0:
            print(f"\n   🚨 Extreme Level Changes: {management_analysis['extreme_changes']:,}")
            extreme_rate = management_analysis['extreme_changes'] / management_analysis.get('total_analyzed', 1)
            if extreme_rate > 0.05:
                print("   🔴 HIGH RATE of extreme level changes detected")
            else:
                print("   🟡 Some extreme level changes detected")
        
        avg_change = management_analysis.get('avg_level_change', 0)
        print(f"   Average Level Change: {avg_change:.2f}")
    print()
    
    # Function Change Analysis
    print("🔄 FUNCTION CHANGE ANALYSIS:")
    print("=" * 35)
    
    if function_analysis.get('no_data', False):
        print("   ⚠️  No function change data available")
    else:
        total = function_analysis.get('total_analyzed', 0)
        print(f"   Total Pathways Analyzed: {total:,}")
        
        if 'change_types' in function_analysis:
            print("\n   Change Type Distribution:")
            for ctype, count in function_analysis['change_types'].items():
                percentage = (count / total) * 100 if total > 0 else 0
                print(f"   • {ctype.replace('_', ' ').title()}: {count:,} ({percentage:.1f}%)")
        
        cross_func_rate = function_analysis.get('cross_function_rate', 0)
        print(f"\n   Cross-Function Rate: {cross_func_rate*100:.1f}%")
        
        suspicious = function_analysis.get('suspicious_cross_function_moves', 0)
        if suspicious > 0:
            suspicious_rate = suspicious / total if total > 0 else 0
            print(f"   🚨 Suspicious High-Confidence Cross-Function: {suspicious:,} ({suspicious_rate*100:.2f}%)")
            if suspicious_rate > 0.02:  # >2%
                print("   🔴 HIGH RATE of unrealistic cross-function moves")
    print()
    
    # Overall Model Health Assessment
    print("🏥 OVERALL MODEL HEALTH ASSESSMENT:")
    print("=" * 45)
    
    # Calculate overall health score
    health_factors = []
    
    # Factor 1: Confidence distribution (should be well-distributed)
    if dist['very_high_confidence'] < 0.1:  # <10% very high is good
        health_factors.append(("Confidence Distribution", "GOOD", "Well-distributed confidence scores"))
    elif dist['very_high_confidence'] < 0.2:
        health_factors.append(("Confidence Distribution", "MODERATE", "Moderately high confidence concentration"))
    else:
        health_factors.append(("Confidence Distribution", "POOR", "Too many high-confidence predictions"))
    
    # Factor 2: Business rule violations
    violation_rate = business_analysis.get('violation_rate', 0)
    if violation_rate < 0.05:
        health_factors.append(("Business Logic", "GOOD", "Low violation rate"))
    elif violation_rate < 0.1:
        health_factors.append(("Business Logic", "MODERATE", "Moderate violation rate"))
    else:
        health_factors.append(("Business Logic", "POOR", "High violation rate"))
    
    # Factor 3: Extreme confidence scores
    if concerns['unrealistic_precision'] < 0.01:
        health_factors.append(("Confidence Realism", "GOOD", "Realistic confidence levels"))
    elif concerns['unrealistic_precision'] < 0.05:
        health_factors.append(("Confidence Realism", "MODERATE", "Some unrealistic confidence"))
    else:
        health_factors.append(("Confidence Realism", "POOR", "Many unrealistic confidence scores"))
    
    print("   Health Factor Analysis:")
    good_count = sum(1 for _, rating, _ in health_factors if rating == "GOOD")
    
    for factor, rating, description in health_factors:
        emoji = "✅" if rating == "GOOD" else "🟡" if rating == "MODERATE" else "❌"
        print(f"   {emoji} {factor}: {rating} - {description}")
    
    print()
    
    # Overall recommendation
    if good_count == len(health_factors):
        overall = "🟢 EXCELLENT - Model ready for production"
    elif good_count >= len(health_factors) // 2:
        overall = "🟡 MODERATE - Monitor and consider improvements"
    else:
        overall = "🔴 POOR - Model needs significant improvement"
    
    print(f"   🎯 OVERALL ASSESSMENT: {overall}")
    
    # Specific recommendations
    print("\n   📋 SPECIFIC RECOMMENDATIONS:")
    if concerns['unrealistic_precision'] > 0.05:
        print("   • Investigate model calibration - too many >99% confidence scores")
    if business_analysis.get('violation_rate', 0) > 0.1:
        print("   • Review training data for business logic consistency")
    if dist['very_high_confidence'] > 0.2:
        print("   • Consider ensemble methods to improve confidence calibration")
    if management_analysis.get('extreme_changes', 0) / metadata.get('total_predictions', 1) > 0.05:
        print("   • Add management level constraints to model training")
    
    print()


def export_corpus_results(results: Dict[str, Any], filename: str):
    """Export corpus analysis results to CSV."""
    try:
        import pandas as pd
        
        # Export raw predictions
        predictions_df = pd.DataFrame(results['raw_predictions'])
        
        # Add analysis flags
        business_violations = {v['source_job'] + '_' + v['target_job']: v['violations'] 
                             for v in results['business_rule_analysis'].get('violations', [])}
        
        predictions_df['business_violations'] = predictions_df.apply(
            lambda row: business_violations.get(row['source_job'] + '_' + row['target_job'], []), 
            axis=1
        )
        
        # Export to CSV
        output_path = filename if filename.endswith('.csv') else f"{filename}.csv"
        predictions_df.to_csv(output_path, index=False)
        
        print(f"📄 Corpus analysis results exported to: {output_path}")
        print(f"   Records: {len(predictions_df):,}")
        
        # Get file size
        try:
            file_size = os.path.getsize(output_path) / 1024 / 1024  # MB
            print(f"   File size: {file_size:.2f} MB")
        except:
            print(f"   File created successfully")
        
    except Exception as e:
        print(f"❌ Failed to export results: {e}")


def run_interactive_mode(predictor, job_profiles):
    """Run the interactive mode for testing predictions."""
    # Show sample job profiles with formatted names
    print("Sample Job Profiles:")
    for i, (_, row) in enumerate(job_profiles.head(10).iterrows()):
        job_id = row['job_profile_id']
        formatted_name = predictor.get_formatted_job_name(job_id)
        print(f"  {job_id}: {formatted_name}")
    print()
    
    # Test predictions
    while True:
        print("🔮 Interactive Pathway Prediction Test")
        print("-" * 40)
        
        # Get source job
        from_job = input("Enter source job profile ID (or 'quit' to exit): ").strip()
        if from_job.lower() == 'quit':
            break
        
        # Validate source job
        if from_job not in job_profiles['job_profile_id'].values:
            print(f"❌ Job profile '{from_job}' not found.")
            continue
        
        # Ask for prediction mode
        print("\nPrediction options:")
        print("1. Use most similar jobs (recommended)")
        print("2. Enter custom target jobs")
        choice = input("Choose option (1 or 2): ").strip()
        
        if choice == '1':
            # Get number of similar jobs
            try:
                top_n = int(input("How many similar jobs to analyze? (default 5): ").strip() or "5")
                to_jobs = predictor.get_most_similar_jobs(from_job, top_n)
                if not to_jobs:
                    continue
            except ValueError:
                print("❌ Please enter a valid number.")
                continue
                
        elif choice == '2':
            # Get target jobs
            to_jobs_input = input("Enter target job profile ID(s) (comma-separated): ").strip()
            to_jobs = [job.strip() for job in to_jobs_input.split(',')]
            
            # Validate target jobs
            invalid_jobs = [job for job in to_jobs if job not in job_profiles['job_profile_id'].values]
            if invalid_jobs:
                print(f"❌ Invalid job profile(s): {invalid_jobs}")
                continue
        else:
            print("❌ Invalid choice. Please select 1 or 2.")
            continue
        
        print()
        print(f"🎯 Predicting pathways: {from_job} → {to_jobs}")
        print()
        
        # Make predictions
        results = predictor.predict_pathways(from_job, to_jobs)
        
        if 'error' in results:
            print(f"❌ Prediction failed: {results['error']}")
            continue
        
        # Display results
        display_prediction_results(predictor, from_job, results)
        print()
        input("Press Enter to continue...")


def run_validation_check(db_path: Path, from_job_id: str, predictions: List[Dict[str, Any]]) -> None:
    """Run production validation on predictions."""
    try:
        # Import validation module
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        from skill_similarity_engine.validation.production_validator import ProductionValidator
        
        # Transform predictions to expected format
        validation_predictions = []
        for pred in predictions:
            validation_predictions.append({
                'from_job_id': from_job_id,
                'to_job_id': pred['to_job_id'],
                'agreement_rate': pred['agreement_rate'],
                'predicted_movements': pred['predicted_movements']
            })
        
        validator = ProductionValidator(str(db_path))
        validation_results = validator.validate_business_logic(validation_predictions)
        
        # Display detailed validation analysis
        total = validation_results['total_predictions']
        failed = validation_results['business_rules_failed']
        warnings = len(validation_results['warnings'])
        
        print(f"📊 DETAILED VALIDATION ANALYSIS:")
        print(f"=" * 60)
        print(f"🔍 Validating {total} pathway predictions...")
        print()
        
        # Show validation for each prediction
        for i, pred in enumerate(validation_predictions, 1):
            from_job = pred['from_job_id']
            to_job = pred['to_job_id']
            feasibility = pred['agreement_rate']
            movements = pred['predicted_movements']
            
            print(f"🎯 Pathway {i}: {from_job} → {to_job}")
            print(f"   Feasibility: {feasibility:.1%}, Expected Movements: {movements:.2f}")
            
            # Check each validation rule individually
            rule_results = []
            
            # Rule 1: Same job check
            if from_job == to_job:
                if feasibility > 0.1:
                    rule_results.append("❌ SAME JOB: High feasibility for same-job movement")
                else:
                    rule_results.append("✅ SAME JOB: Appropriately low feasibility")
            else:
                rule_results.append("✅ DIFFERENT JOBS: Valid pathway")
            
            # Rule 2: Management level check
            mgmt_check = get_management_level_details(db_path, from_job, to_job, feasibility)
            rule_results.append(mgmt_check)
            
            # Rule 3: Function change check
            function_check = get_function_change_details(db_path, from_job, to_job, feasibility)
            rule_results.append(function_check)
            
            # Rule 4: Extreme feasibility check
            if feasibility > 0.98:
                rule_results.append("⚠️  EXTREME FEASIBILITY: >98% should be investigated")
            elif feasibility > 0.95:
                rule_results.append("✅ HIGH FEASIBILITY: Within expected range")
            else:
                rule_results.append("✅ NORMAL FEASIBILITY: Within expected range")
            
            # Display rule results
            for rule_result in rule_results:
                print(f"     {rule_result}")
            
            print()
        
        print("📈 VALIDATION SUMMARY:")
        print(f"   Total Predictions Analyzed: {total}")
        print(f"   ✅ Business Rules Passed: {total - failed}")
        print(f"   ❌ Business Rules Failed: {failed}")
        print(f"   ⚠️  Warnings Generated: {warnings}")
        
        if failed > 0:
            print(f"\n🚨 FAILED VALIDATIONS:")
            for i, failure in enumerate(validation_results['failed_validations'], 1):
                print(f"   {i}. {failure['rule']}: {failure['from_job']} → {failure['to_job']}")
                print(f"      Feasibility: {failure['feasibility']:.1%}")
                print(f"      Issue: {failure['reason']}")
                print()
        
        if warnings > 0:
            print(f"💡 VALIDATION WARNINGS:")
            for i, warning in enumerate(validation_results['warnings'], 1):
                print(f"   {i}. {warning['rule']}: {warning['from_job']} → {warning['to_job']}")
                print(f"      Feasibility: {warning['feasibility']:.1%}")
                print(f"      Note: {warning.get('reason', 'Review recommended')}")
                print()
        
        # Overall assessment with detailed reasoning
        failure_rate = failed / total if total > 0 else 0
        print(f"🎯 OVERALL ASSESSMENT:")
        print(f"   Failure Rate: {failure_rate:.1%} ({failed}/{total})")
        
        if failure_rate > 0.1:
            print(f"   🔴 STATUS: HIGH FAILURE RATE")
            print(f"   📋 ACTION: Model retraining strongly recommended")
            print(f"   💡 REASON: >10% of predictions violate business logic")
        elif failure_rate > 0.05:
            print(f"   🟡 STATUS: MODERATE FAILURE RATE") 
            print(f"   📋 ACTION: Monitor closely, consider model adjustments")
            print(f"   💡 REASON: 5-10% failure rate indicates potential issues")
        else:
            print(f"   🟢 STATUS: LOW FAILURE RATE")
            print(f"   📋 ACTION: Model performing well, continue monitoring")
            print(f"   💡 REASON: <5% failure rate is within acceptable range")
            
    except ImportError as e:
        print(f"❌ Validation module not available: {e}")
    except Exception as e:
        print(f"❌ Validation failed: {e}")


def get_management_level_details(db_path: Path, from_job: str, to_job: str, feasibility: float) -> str:
    """Get detailed management level validation information."""
    try:
        query = """
        SELECT 
            from_arch.ManagementLevel as from_level,
            to_arch.ManagementLevel as to_level,
            from_arch.JobFunction as from_function,
            to_arch.JobFunction as to_function,
            from_arch.JobProfile as from_title,
            to_arch.JobProfile as to_title
        FROM core_job_architecture from_arch
        JOIN core_job_architecture to_arch ON 1=1
        WHERE from_arch.JobProfileID = ? AND to_arch.JobProfileID = ?
        """
        
        with sqlite3.connect(str(db_path)) as conn:
            result = conn.execute(query, (from_job, to_job)).fetchone()
            
            if not result:
                return "⚠️  MANAGEMENT LEVEL: Cannot validate (missing job data)"
            
            from_level, to_level, from_function, to_function, from_title, to_title = result
            
            # Extract numeric levels if possible
            try:
                from_num = int(from_level.split()[-1]) if from_level else 0
                to_num = int(to_level.split()[-1]) if to_level else 0
                level_diff = from_num - to_num
                
                # Detailed analysis
                if level_diff == 0:
                    return f"✅ MANAGEMENT LEVEL: Same level ({from_level}) - appropriate"
                elif level_diff == 1:
                    return f"✅ MANAGEMENT LEVEL: 1 level promotion ({from_level} → {to_level}) - normal progression"
                elif level_diff == -1:
                    return f"✅ MANAGEMENT LEVEL: 1 level step-down ({from_level} → {to_level}) - acceptable"
                elif level_diff > 1:
                    if feasibility > 0.8 and from_function == to_function:
                        return f"❌ MANAGEMENT LEVEL: {level_diff} level promotion with {feasibility:.1%} feasibility seems unrealistic"
                    else:
                        return f"✅ MANAGEMENT LEVEL: {level_diff} level promotion - feasibility {feasibility:.1%} is reasonable"
                elif level_diff < -2:
                    if feasibility > 0.8:
                        return f"❌ MANAGEMENT LEVEL: {abs(level_diff)} level demotion with {feasibility:.1%} feasibility is suspicious"
                    else:
                        return f"✅ MANAGEMENT LEVEL: {abs(level_diff)} level demotion - low feasibility {feasibility:.1%} is appropriate"
                else:
                    return f"✅ MANAGEMENT LEVEL: {level_diff} level change - within reasonable range"
                    
            except (ValueError, IndexError, AttributeError):
                return f"⚠️  MANAGEMENT LEVEL: Cannot parse levels ({from_level} → {to_level})"
                
    except Exception as e:
        return f"⚠️  MANAGEMENT LEVEL: Validation error - {str(e)[:50]}"


def get_function_change_details(db_path: Path, from_job: str, to_job: str, feasibility: float) -> str:
    """Get detailed job function change validation information."""
    try:
        query = """
        SELECT 
            from_arch.JobFunction as from_function,
            to_arch.JobFunction as to_function,
            from_arch.JobSubFunction as from_sub_function,
            to_arch.JobSubFunction as to_sub_function
        FROM core_job_architecture from_arch
        JOIN core_job_architecture to_arch ON 1=1
        WHERE from_arch.JobProfileID = ? AND to_arch.JobProfileID = ?
        """
        
        with sqlite3.connect(str(db_path)) as conn:
            result = conn.execute(query, (from_job, to_job)).fetchone()
            
            if not result:
                return "⚠️  JOB FUNCTION: Cannot validate (missing job data)"
            
            from_function, to_function, from_sub_function, to_sub_function = result
            
            # Same function analysis
            if from_function == to_function:
                if from_sub_function == to_sub_function:
                    return f"✅ JOB FUNCTION: Same function & sub-function ({from_function}) - natural progression"
                else:
                    return f"✅ JOB FUNCTION: Same function ({from_function}), different specialization - good mobility"
            
            # Cross-functional analysis
            else:
                if feasibility > 0.95:
                    return f"⚠️  JOB FUNCTION: Cross-functional move ({from_function} → {to_function}) with {feasibility:.1%} feasibility seems high"
                elif feasibility > 0.85:
                    return f"✅ JOB FUNCTION: Cross-functional move ({from_function} → {to_function}) - feasibility {feasibility:.1%} is reasonable"
                else:
                    return f"✅ JOB FUNCTION: Cross-functional move ({from_function} → {to_function}) - appropriately lower feasibility"
                    
    except Exception as e:
        return f"⚠️  JOB FUNCTION: Validation error - {str(e)[:50]}"


if __name__ == "__main__":
    main()