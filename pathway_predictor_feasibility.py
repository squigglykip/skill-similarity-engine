#!/usr/bin/env python3
"""
Pathway Feasibility Predictor - Multi-Dimensional Feasibility Assessment

This module implements a comprehensive feasibility assessment framework for job pathway predictions.
Key principles:
1. Fail-fast approach: Insufficient historical data = Low feasibility  
2. Multi-dimensional assessment: Volume, confidence, model agreement, career logic
3. Binary feasibility output: High or Low feasibility with clear reasoning

Author: AI Assistant
Created: 2025-01-27
"""

import argparse
import json
import logging
import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
import numpy as np
import joblib
from tqdm import tqdm
import yaml
import random

# Import existing modules for feature engineering consistency
sys.path.append('src')
from skill_similarity_engine.models.movement_ml_trainer import MovementMLTrainer

class PathwayFeasibilityPredictor:
    """
    Advanced pathway feasibility predictor with multi-dimensional assessment.
    
    Implements fail-fast approach for data-poor predictions and comprehensive
    feasibility scoring based on volume, confidence, model agreement, and business logic.
    """
    
    def __init__(self, db_path: str = "models/2025-Q3/business_context.sqlite", 
                 models_dir: str = "models/2025-Q3"):
        """
        Initialize the feasibility predictor.
        
        Args:
            db_path: Path to the SQLite database
            models_dir: Directory containing trained ML models
        """
        self.db_path = db_path
        self.models_dir = models_dir
        self.models = {}
        self.feature_columns = []
        self.ml_trainer = None
        
        # Feasibility thresholds (Option A - Balanced approach)
        self.SYNTHETIC_FEATURE_THRESHOLD = 0.85  # >85% synthetic = fail fast
        self.MIN_VOLUME_THRESHOLD = 0.3  # <0.3 movements/year = low feasibility
        self.MIN_CONFIDENCE_THRESHOLD = 0.6  # <60% confidence = low feasibility  
        self.MAX_MODEL_DISAGREEMENT = 0.3  # Std dev threshold for model disagreement
        
        # Load models and initialize trainer
        self._load_models()
        self._initialize_ml_trainer()
        
    def _load_models(self):
        """Load trained ML models and metadata."""
        # Try multiple metadata file locations
        metadata_paths = [
            Path(self.models_dir) / "model_metadata.json",
            Path("ml-training-metadata.json"),
            Path(self.models_dir) / "ml-training-metadata.json"
        ]
        
        metadata_path = None
        for path in metadata_paths:
            if path.exists():
                metadata_path = path
                break
                
        if not metadata_path:
            raise FileNotFoundError(f"Model metadata not found in: {metadata_paths}")
            
        # Load metadata
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
            
        self.feature_columns = metadata['feature_columns']
        
        # Define model files based on standard naming convention
        model_files = {
            'Random Forest': 'random_forest_model.joblib',
            'Gradient Boosting': 'gradient_boosting_model.joblib', 
            'XGBoost': 'xgboost_model.joblib'
        }
        
        # Load each model
        for model_name, filename in model_files.items():
            model_path = Path(self.models_dir) / filename
            if model_path.exists():
                self.models[model_name] = joblib.load(model_path)
            else:
                pass  # Silent model loading for scale testing
                
        # Removed verbose output for scale testing
        
    def _initialize_ml_trainer(self):
        """Initialize MovementMLTrainer for feature engineering consistency."""
        # Suppress verbose logging during initialization
        logging.getLogger().setLevel(logging.ERROR)
        
        # Load configuration
        config_path = Path("config/modules/models/movement_ml_training.yaml")
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            pass  # Silent loading for scale testing
        else:
            config = {}
            
        # Initialize trainer
        self.ml_trainer = MovementMLTrainer(self.db_path, config)
        
        # Reset logging level
        logging.getLogger().setLevel(logging.INFO)
        
    def load_and_cache_data(self, verbose: bool = False):
        """Load and cache all necessary data for predictions."""
        if verbose:
            print("📊 Loading movement patterns and job data...")
        
        # Suppress verbose logging during data loading
        logging.getLogger().setLevel(logging.ERROR)
        
        # Load data using MovementMLTrainer methods
        self.movement_patterns = self.ml_trainer.load_movement_patterns_data()
        if verbose:
            print(f"✅ Loaded {len(self.movement_patterns):,} movement patterns from database")
        
        self.job_architecture = self.ml_trainer.load_job_architecture_data()  
        if verbose:
            print(f"✅ Loaded {len(self.job_architecture):,} job profiles from database")
        
        self.job_transitions = self.ml_trainer.aggregate_movement_patterns_to_job_level(self.movement_patterns)
        if verbose:
            print(f"✅ Aggregated to {len(self.job_transitions):,} job profile transition pairs")
        
        self.source_mobility_scores, self.target_mobility_scores = self.ml_trainer.calculate_mobility_scores(self.job_transitions)
        if verbose:
            print(f"✅ Calculated mobility for {len(self.source_mobility_scores):,} source and {len(self.target_mobility_scores):,} target roles")
        
        # Reset logging level
        logging.getLogger().setLevel(logging.INFO)
        
        if verbose:
            print(f"✅ Cached {len(self.movement_patterns):,} movement patterns, {len(self.job_architecture):,} jobs, {len(self.job_transitions):,} job transitions")
        
    def predict_pathway_feasibility(self, from_job_id: str, to_job_id: str) -> Dict[str, Any]:
        """
        Predict pathway feasibility with comprehensive multi-dimensional assessment.
        
        Args:
            from_job_id: Source job profile ID
            to_job_id: Target job profile ID
            
        Returns:
            Dictionary containing feasibility assessment, reasoning, and detailed metrics
        """
        try:
            # Get transition data for this job pair
            transition_data = self.job_transitions[
                (self.job_transitions['from_job_profile_id'] == from_job_id) &
                (self.job_transitions['to_job_profile_id'] == to_job_id)
            ].copy()
            
            if transition_data.empty:
                # Create synthetic row for unseen transitions
                from_job_info = self.job_architecture[self.job_architecture['JobProfileID'] == from_job_id]
                to_job_info = self.job_architecture[self.job_architecture['JobProfileID'] == to_job_id]
                
                if from_job_info.empty or to_job_info.empty:
                    return self._create_error_result(from_job_id, to_job_id, "Job IDs not found in architecture")
                
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
            
            # Create ML features using the exact same method as training (suppress verbose output)
            import sys
            from io import StringIO
            
            # Capture stdout to suppress all output
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            sys.stdout = StringIO()
            sys.stderr = StringIO()
            
            try:
                features_df = self.ml_trainer.create_ml_features(
                    transition_data, self.source_mobility_scores, self.target_mobility_scores, self.job_architecture
                )
            finally:
                # Always restore stdout/stderr
                sys.stdout = old_stdout
                sys.stderr = old_stderr
            
            if features_df.empty:
                return self._create_error_result(from_job_id, to_job_id, "Feature generation failed")
                
            # Extract feature values for synthetic percentage calculation
            feature_values = features_df.iloc[0].to_dict()
            
            # Calculate synthetic feature percentage  
            synthetic_pct = self._calculate_synthetic_feature_percentage(feature_values)
            
            # FAIL FAST: Check for insufficient historical data
            if synthetic_pct > self.SYNTHETIC_FEATURE_THRESHOLD:
                return self._create_low_feasibility_result(
                    from_job_id, to_job_id, "INSUFFICIENT_HISTORICAL_DATA",
                    f"Model relies on {synthetic_pct:.1%} synthetic features (threshold: {self.SYNTHETIC_FEATURE_THRESHOLD:.1%})",
                    synthetic_pct=synthetic_pct
                )
            
            # Filter features to match training columns (remove non-feature columns)
            model_features_df = features_df[self.feature_columns].copy()
            
            # Run ensemble predictions
            raw_predictions = []
            model_predictions = {}
            
            for model_name, model in self.models.items():
                try:
                    prediction = model.predict(model_features_df)[0]
                    raw_predictions.append(prediction)
                    model_predictions[model_name] = float(prediction)
                except Exception as e:
                    # Silent failure for scale testing
                    continue
                    
            if not raw_predictions:
                return self._create_error_result(from_job_id, to_job_id, "All model predictions failed")
                
            # Calculate ensemble metrics
            ensemble_prediction = np.mean(raw_predictions)
            predicted_annual_movements = max(0.0, ensemble_prediction)
            
            # Calculate model agreement (confidence)
            if len(raw_predictions) > 1:
                prediction_std = np.std(raw_predictions)
                prediction_mean = np.mean(raw_predictions) 
                coefficient_of_variation = prediction_std / (prediction_mean + 1e-6)
                confidence_score = max(0.0, min(1.0, 1.0 - coefficient_of_variation))
                model_disagreement = prediction_std
            else:
                confidence_score = 0.5  # Medium confidence for single model
                model_disagreement = 0.0
                coefficient_of_variation = 0.0
                
            # FEASIBILITY ASSESSMENT
            feasibility_result = self._assess_feasibility(
                predicted_annual_movements=predicted_annual_movements,
                confidence_score=confidence_score,
                model_disagreement=model_disagreement,
                synthetic_pct=synthetic_pct,
                from_job_id=from_job_id,
                to_job_id=to_job_id
            )
            
            # Create comprehensive result
            result = {
                'from_job_id': from_job_id,
                'to_job_id': to_job_id,
                'feasibility_assessment': feasibility_result['feasibility'],
                'feasibility_category': feasibility_result['category'], 
                'feasibility_reasoning': feasibility_result['reasoning'],
                'red_flags': feasibility_result['red_flags'],
                'predicted_annual_movements': round(predicted_annual_movements, 3),
                'confidence_score': round(confidence_score, 3),
                'model_disagreement_std': round(model_disagreement, 4),
                'synthetic_feature_percentage': round(synthetic_pct, 3),
                'model_predictions': model_predictions,
                'coefficient_of_variation': round(coefficient_of_variation, 4),
                'feature_count': len(self.feature_columns),
                'assessment_status': 'success'
            }
            
            return result
            
        except Exception as e:
            return self._create_error_result(from_job_id, to_job_id, str(e))
            
    def _calculate_synthetic_feature_percentage(self, feature_values: Dict[str, float]) -> float:
        """
        Calculate the percentage of features that are synthetic/default values.
        
        This helps identify when the model lacks sufficient historical data.
        """
        synthetic_indicators = [
            # Movement pattern features (would be 0.0 if no history)
            feature_values.get('total_movement_count', 0) == 0,
            feature_values.get('avg_movements_per_year', 0) == 0,
            feature_values.get('transition_frequency', 0) == 0,
            
            # Recency features (would be default if no recent data)
            feature_values.get('recency_weighted_activity', 0) == 0,
            feature_values.get('recency_boost', 1) == 1,  # Default value
            
            # Timing features (would be defaults if no history)
            feature_values.get('avg_days_between', 365) == 365,  # Default
            feature_values.get('years_active', 1) == 1,  # Default
            
            # Mobility features (would be 0 if calculated from empty data)
            feature_values.get('source_mobility_score', 0) == 0,
            feature_values.get('target_mobility_score', 0) == 0,
        ]
        
        # Calculate percentage of synthetic features
        total_indicators = len(synthetic_indicators)
        synthetic_count = sum(synthetic_indicators)
        
        return synthetic_count / total_indicators if total_indicators > 0 else 0.0
        
    def _assess_feasibility(self, predicted_annual_movements: float, confidence_score: float,
                          model_disagreement: float, synthetic_pct: float,
                          from_job_id: str, to_job_id: str) -> Dict[str, Any]:
        """
        Multi-dimensional feasibility assessment using fail-fast approach.
        """
        red_flags = []
        reasoning_parts = []
        
        # Volume feasibility check
        if predicted_annual_movements < self.MIN_VOLUME_THRESHOLD:
            red_flags.append("VOLUME_TOO_LOW")
            reasoning_parts.append(f"Predicted volume too low ({predicted_annual_movements:.2f} < {self.MIN_VOLUME_THRESHOLD})")
            
        # Confidence check
        if confidence_score < self.MIN_CONFIDENCE_THRESHOLD:
            red_flags.append("LOW_CONFIDENCE")
            reasoning_parts.append(f"Model confidence too low ({confidence_score:.1%} < {self.MIN_CONFIDENCE_THRESHOLD:.1%})")
            
        # Model disagreement check
        if model_disagreement > self.MAX_MODEL_DISAGREEMENT:
            red_flags.append("MODEL_DISAGREEMENT")
            reasoning_parts.append(f"High model disagreement (std: {model_disagreement:.3f})")
            
        # Career reversal check
        career_reversal = self._check_career_reversal(from_job_id, to_job_id)
        if career_reversal:
            red_flags.append("CAREER_REVERSAL")
            reasoning_parts.append(career_reversal)
            
        # Synthetic data warning (already handled in fail-fast, but flag if significant)
        if synthetic_pct > 0.4:  # 40% threshold for warning
            red_flags.append("HIGH_SYNTHETIC_DATA")
            reasoning_parts.append(f"Limited historical data ({synthetic_pct:.1%} synthetic features)")
            
        # Determine overall feasibility
        if len(red_flags) == 0:
            feasibility = "HIGH_FEASIBILITY"
            category = "Highly Feasible"
            reasoning = "Strong model support with sufficient historical data"
        elif len(red_flags) == 1 and "HIGH_SYNTHETIC_DATA" in red_flags:
            feasibility = "MODERATE_FEASIBILITY" 
            category = "Moderately Feasible"
            reasoning = "Limited historical data but model shows reasonable confidence"
        else:
            feasibility = "LOW_FEASIBILITY"
            category = "Low Feasibility"
            reasoning = "; ".join(reasoning_parts)
            
        return {
            'feasibility': feasibility,
            'category': category,
            'reasoning': reasoning,
            'red_flags': red_flags
        }
        
    def _check_career_reversal(self, from_job_id: str, to_job_id: str) -> Optional[str]:
        """Check for management level demotions (career reversals)."""
        try:
            from_job = self.job_architecture[self.job_architecture['JobProfileID'] == from_job_id].iloc[0]
            to_job = self.job_architecture[self.job_architecture['JobProfileID'] == to_job_id].iloc[0]
            
            from_level_str = str(from_job['ManagementLevel']).replace('Group ', '').replace('Group', '')
            to_level_str = str(to_job['ManagementLevel']).replace('Group ', '').replace('Group', '')
            
            # Skip if either level is NA/missing
            if from_level_str in ['NA', 'nan', ''] or to_level_str in ['NA', 'nan', '']:
                return None
                
            from_level = int(from_level_str)
            to_level = int(to_level_str)
            
            # Check for demotion (Group 1 = junior, Group 5+ = senior)
            if from_level > to_level:  # Higher group number = higher level, so this is a demotion
                return f"Management demotion (Group {from_level} → Group {to_level})"
                
        except (ValueError, IndexError, KeyError):
            pass  # Skip if parsing fails
            
        return None
        
    def _create_low_feasibility_result(self, from_job_id: str, to_job_id: str, 
                                     reason: str, details: str, **kwargs) -> Dict[str, Any]:
        """Create standardized low feasibility result."""
        return {
            'from_job_id': from_job_id,
            'to_job_id': to_job_id,
            'feasibility_assessment': 'LOW_FEASIBILITY',
            'feasibility_category': 'Not Feasible',
            'feasibility_reasoning': details,
            'red_flags': [reason],
            'predicted_annual_movements': 0.0,
            'confidence_score': 0.0,
            'model_disagreement_std': 0.0,
            'assessment_status': 'low_feasibility',
            **kwargs
        }
        
    def _create_error_result(self, from_job_id: str, to_job_id: str, error: str) -> Dict[str, Any]:
        """Create standardized error result."""
        return {
            'from_job_id': from_job_id,
            'to_job_id': to_job_id,
            'feasibility_assessment': 'ERROR',
            'feasibility_category': 'Assessment Failed',
            'feasibility_reasoning': f"Prediction error: {error}",
            'red_flags': ['PREDICTION_ERROR'],
            'assessment_status': 'error'
        }
        
    def run_single_prediction(self, from_job_id: str, to_job_id: str, verbose: bool = True) -> Dict[str, Any]:
        """Run feasibility assessment for a single job transition."""
        self.load_and_cache_data(verbose=verbose)
        
        result = self.predict_pathway_feasibility(from_job_id, to_job_id)
        
        # Print formatted result only if verbose
        if verbose:
            self._print_single_result(result)
        
        return result
        
    def run_corpus_analysis(self, sample_size: int = 100, verbose: bool = True) -> Dict[str, Any]:
        """Run feasibility analysis on a random sample of job transitions."""
        self.load_and_cache_data(verbose=verbose)
        
        if verbose:
            print(f"\n🔬 PATHWAY FEASIBILITY ANALYSIS (Option A - Balanced)")
            print("=" * 80)
            print(f"📊 Sample Size: {sample_size:,} predictions")
            print(f"🚨 Feasibility Thresholds:")
            print(f"   • Synthetic Features: >{self.SYNTHETIC_FEATURE_THRESHOLD:.1%} = Fail Fast")
            print(f"   • Min Volume: <{self.MIN_VOLUME_THRESHOLD} movements/year")
            print(f"   • Min Confidence: <{self.MIN_CONFIDENCE_THRESHOLD:.1%}")
            print(f"   • Model Disagreement: >{self.MAX_MODEL_DISAGREEMENT} std dev")
            print("=" * 80)
        
        # Generate random job pairs
        job_ids = self.job_architecture['JobProfileID'].tolist()
        job_pairs = []
        
        for _ in range(sample_size):
            from_job = str(random.choice(job_ids))
            to_job = str(random.choice(job_ids))
            if from_job != to_job:  # Avoid self-transitions
                job_pairs.append((from_job, to_job))
                
        # Run predictions with progress bar (always show for scale testing)
        results = []
        progress_bar = tqdm(job_pairs, desc="🔮 Analyzing feasibility", 
                          unit="prediction", leave=True)
        
        for from_job_id, to_job_id in progress_bar:
            result = self.predict_pathway_feasibility(from_job_id, to_job_id)
            results.append(result)
            
            # Update progress description with current feasibility (only if verbose)
            if verbose and result['assessment_status'] == 'success':
                feasibility = result['feasibility_assessment']
                progress_bar.set_postfix({"Latest": feasibility})
                
        # Analyze results
        analysis = self._analyze_corpus_results(results)
        
        # Print comprehensive analysis (only if verbose)
        if verbose:
            self._print_corpus_analysis(analysis, len(results))
        
        return {
            'analysis': analysis,
            'raw_results': results,
            'sample_size': len(results)
        }
        
    def _analyze_corpus_results(self, results: List[Dict]) -> Dict[str, Any]:
        """Analyze corpus prediction results for patterns and distributions."""
        # Filter successful predictions
        successful = [r for r in results if r['assessment_status'] == 'success']
        failed = [r for r in results if r['assessment_status'] == 'error']
        low_feasibility_data = [r for r in results if r['assessment_status'] == 'low_feasibility']
        
        # Feasibility distribution
        feasibility_counts = {}
        red_flag_counts = {}
        
        for result in results:
            feasibility = result.get('feasibility_assessment', 'UNKNOWN')
            feasibility_counts[feasibility] = feasibility_counts.get(feasibility, 0) + 1
            
            # Count red flags
            flags = result.get('red_flags', [])
            for flag in flags:
                red_flag_counts[flag] = red_flag_counts.get(flag, 0) + 1
                
        # Metrics for successful predictions
        if successful:
            volumes = [r['predicted_annual_movements'] for r in successful]
            confidences = [r['confidence_score'] for r in successful]
            synthetics = [r['synthetic_feature_percentage'] for r in successful]
            disagreements = [r['model_disagreement_std'] for r in successful]
            
            volume_stats = {
                'min': min(volumes), 'max': max(volumes), 'mean': np.mean(volumes),
                'median': np.median(volumes), 'std': np.std(volumes)
            }
            
            confidence_stats = {
                'min': min(confidences), 'max': max(confidences), 'mean': np.mean(confidences),
                'median': np.median(confidences), 'std': np.std(confidences)
            }
            
            synthetic_stats = {
                'min': min(synthetics), 'max': max(synthetics), 'mean': np.mean(synthetics),
                'median': np.median(synthetics), 'std': np.std(synthetics)
            }
            
        else:
            volume_stats = confidence_stats = synthetic_stats = {}
            
        return {
            'total_predictions': len(results),
            'successful_predictions': len(successful),
            'failed_predictions': len(failed),
            'low_feasibility_data_poor': len(low_feasibility_data),
            'feasibility_distribution': feasibility_counts,
            'red_flag_distribution': red_flag_counts,
            'volume_statistics': volume_stats,
            'confidence_statistics': confidence_stats,
            'synthetic_feature_statistics': synthetic_stats
        }
        
    def _print_single_result(self, result: Dict[str, Any]):
        """Print formatted single prediction result."""
        print(f"\n🔮 PATHWAY FEASIBILITY ASSESSMENT")
        print("=" * 60)
        print(f"📋 Transition: Job {result['from_job_id']} → Job {result['to_job_id']}")
        print(f"🎯 Feasibility: {result['feasibility_category']}")
        print(f"💭 Reasoning: {result['feasibility_reasoning']}")
        
        if result['assessment_status'] == 'success':
            print(f"📊 Predicted Volume: {result['predicted_annual_movements']:.3f} movements/year")
            print(f"🎲 Model Confidence: {result['confidence_score']:.1%}")
            print(f"📈 Synthetic Features: {result['synthetic_feature_percentage']:.1%}")
            
        if result.get('red_flags'):
            print(f"🚨 Red Flags: {', '.join(result['red_flags'])}")
            
        print("=" * 60)
        
    def _print_corpus_analysis(self, analysis: Dict[str, Any], total_predictions: int):
        """Print comprehensive corpus analysis results."""
        print(f"\n🔬 FEASIBILITY ANALYSIS RESULTS")
        print("=" * 80)
        
        # Overall summary
        print(f"📊 SUMMARY:")
        print(f"   • Total Predictions: {analysis['total_predictions']:,}")
        print(f"   • Successful Assessments: {analysis['successful_predictions']:,}")
        print(f"   • Failed (Errors): {analysis['failed_predictions']:,}")
        print(f"   • Insufficient Data (Fail Fast): {analysis['low_feasibility_data_poor']:,}")
        
        # Feasibility distribution
        print(f"\n🎯 FEASIBILITY DISTRIBUTION:")
        for feasibility, count in analysis['feasibility_distribution'].items():
            pct = (count / total_predictions) * 100
            print(f"   • {feasibility}: {count:,} ({pct:.1f}%)")
            
        # Red flag analysis
        if analysis['red_flag_distribution']:
            print(f"\n🚨 RED FLAG ANALYSIS:")
            for flag, count in sorted(analysis['red_flag_distribution'].items(), 
                                    key=lambda x: x[1], reverse=True):
                pct = (count / total_predictions) * 100
                print(f"   • {flag}: {count:,} ({pct:.1f}%)")
                
        # Statistical analysis for successful predictions
        if analysis['volume_statistics']:
            print(f"\n📈 PREDICTION STATISTICS (Successful Only):")
            
            vol_stats = analysis['volume_statistics']
            print(f"   📊 Volume (movements/year):")
            print(f"      Min: {vol_stats['min']:.3f}, Max: {vol_stats['max']:.3f}")
            print(f"      Mean: {vol_stats['mean']:.3f}, Median: {vol_stats['median']:.3f}")
            
            conf_stats = analysis['confidence_statistics']
            print(f"   🎲 Model Confidence:")
            print(f"      Min: {conf_stats['min']:.1%}, Max: {conf_stats['max']:.1%}")
            print(f"      Mean: {conf_stats['mean']:.1%}, Median: {conf_stats['median']:.1%}")
            
            syn_stats = analysis['synthetic_feature_statistics']
            print(f"   🔬 Synthetic Features:")
            print(f"      Min: {syn_stats['min']:.1%}, Max: {syn_stats['max']:.1%}")
            print(f"      Mean: {syn_stats['mean']:.1%}, Median: {syn_stats['median']:.1%}")
            
        print("=" * 80)


def main():
    """Main function with argument parsing and execution logic."""
    parser = argparse.ArgumentParser(
        description="Pathway Feasibility Predictor - Multi-Dimensional Assessment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single pathway assessment
  python pathway_predictor_feasibility.py --from-job 123 --to-job 456
  
  # Corpus analysis with custom sample size
  python pathway_predictor_feasibility.py --corpus-analysis --sample-size 500
  
  # Custom database and model paths
  python pathway_predictor_feasibility.py --database custom.db --models-dir custom_models/
        """
    )
    
    # Mode selection
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument('--from-job', type=str, 
                           help='Source job profile ID (requires --to-job)')
    mode_group.add_argument('--corpus-analysis', action='store_true',
                           help='Run analysis on random sample of job transitions')
    
    # Single prediction options
    parser.add_argument('--to-job', type=str,
                       help='Target job profile ID (required with --from-job)')
    
    # Corpus analysis options
    parser.add_argument('--sample-size', type=int, default=100,
                       help='Number of random predictions for corpus analysis (default: 100)')
    
    # Database and model configuration
    parser.add_argument('--database', type=str, 
                       default="models/2025-Q3/business_context.sqlite",
                       help='Path to SQLite database')
    parser.add_argument('--models-dir', type=str, default="models/2025-Q3",
                       help='Directory containing trained ML models')
    
    # Output options
    parser.add_argument('--format', choices=['console', 'json', 'csv'], default='console',
                       help='Output format (default: console)')
    parser.add_argument('--output', type=str,
                       help='Output file path (optional, prints to console if not specified)')
    
    # Note: Thresholds are now hardcoded to Option C calibration for consistency
                       
    args = parser.parse_args()
    
    # Validate arguments
    if args.from_job and not args.to_job:
        parser.error("--from-job requires --to-job")
    if args.to_job and not args.from_job:
        parser.error("--to-job requires --from-job")
        
    try:
        # Initialize predictor
        print("🔮 PathwayFeasibilityPredictor initializing...")
        predictor = PathwayFeasibilityPredictor(
            db_path=args.database,
            models_dir=args.models_dir
        )
        
        # Thresholds are now hardcoded to Option C values - removed override capability for consistency
            
        # Execute based on mode
        if args.from_job:
            # Single pathway prediction
            results = predictor.run_single_prediction(args.from_job, args.to_job)
            
        elif args.corpus_analysis:
            # Corpus analysis - silent for scale testing
            verbose = args.sample_size <= 1000  # Only verbose for small samples
            results = predictor.run_corpus_analysis(args.sample_size, verbose=verbose)
            
            # Print summary for large scale tests
            if args.sample_size > 1000:
                analysis = results['analysis']
                print(f"\n🎯 SCALE TEST SUMMARY ({args.sample_size:,} predictions)")
                print(f"{'='*60}")
                print(f"Feasibility Distribution:")
                for feasibility, count in analysis['feasibility_distribution'].items():
                    pct = (count / analysis['total_predictions']) * 100
                    print(f"  • {feasibility}: {count:,} ({pct:.1f}%)")
                print(f"{'='*60}")
            
        # Handle output formatting
        if args.format != 'console' and args.output:
            output_path = args.output
            
            if args.format == 'json':
                with open(output_path, 'w') as f:
                    json.dump(results, f, indent=2, default=str)
                print(f"💾 Results saved to {output_path}")
                
            elif args.format == 'csv':
                if isinstance(results.get('raw_results'), list):
                    df = pd.DataFrame(results['raw_results'])
                    df.to_csv(output_path, index=False)
                    print(f"💾 Results saved to {output_path}")
                else:
                    print(f"⚠️  Cannot export to CSV - results format not supported")
                    
    except KeyboardInterrupt:
        print("\n⏹️  Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
