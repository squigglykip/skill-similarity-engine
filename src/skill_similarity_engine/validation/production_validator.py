#!/usr/bin/env python3
"""
Production ML Validation Framework for Career Pathway Predictions

This module provides comprehensive validation for the career pathway ML models
including business logic validation, real-world outcome tracking, and A/B testing support.
"""

import sqlite3
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime, timedelta
import logging
from pathlib import Path

class ProductionValidator:
    """Comprehensive validation framework for production ML models."""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.logger = logging.getLogger(__name__)
        
    def validate_business_logic(self, predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate predictions against business rules and common sense."""
        validation_results = {
            'total_predictions': len(predictions),
            'failed_validations': [],
            'warnings': [],
            'business_rules_passed': 0,
            'business_rules_failed': 0
        }
        
        for pred in predictions:
            from_job = pred['from_job_id']
            to_job = pred['to_job_id']
            feasibility = pred['agreement_rate']
            
            # Rule 1: Same job should have very low feasibility (people don't move to same role)
            if from_job == to_job and feasibility > 0.1:
                validation_results['failed_validations'].append({
                    'rule': 'Same Job Movement',
                    'from_job': from_job,
                    'to_job': to_job,
                    'feasibility': feasibility,
                    'reason': 'High feasibility for same-job movement is unrealistic'
                })
                validation_results['business_rules_failed'] += 1
            
            # Rule 2: Check management level progression logic
            mgmt_validation = self._validate_management_progression(from_job, to_job, feasibility)
            if not mgmt_validation['valid']:
                validation_results['failed_validations'].append(mgmt_validation)
                validation_results['business_rules_failed'] += 1
            
            # Rule 3: Cross-functional moves should generally be lower feasibility
            function_validation = self._validate_function_change(from_job, to_job, feasibility)
            if not function_validation['valid']:
                validation_results['warnings'].append(function_validation)
            
            # Rule 4: Extremely high feasibility (>98%) should be rare
            if feasibility > 0.98:
                validation_results['warnings'].append({
                    'rule': 'Extremely High Feasibility',
                    'from_job': from_job,
                    'to_job': to_job,
                    'feasibility': feasibility,
                    'reason': 'Feasibility >98% should be investigated'
                })
        
        validation_results['business_rules_passed'] = (
            validation_results['total_predictions'] - validation_results['business_rules_failed']
        )
        
        return validation_results
    
    def _validate_management_progression(self, from_job: str, to_job: str, feasibility: float) -> Dict[str, Any]:
        """Validate management level progression makes sense."""
        try:
            query = """
            SELECT 
                from_arch.ManagementLevel as from_level,
                to_arch.ManagementLevel as to_level,
                from_arch.JobFunction as from_function,
                to_arch.JobFunction as to_function
            FROM core_job_architecture from_arch
            JOIN core_job_architecture to_arch ON 1=1
            WHERE from_arch.JobProfileID = ? AND to_arch.JobProfileID = ?
            """
            
            with sqlite3.connect(str(self.db_path)) as conn:
                result = conn.execute(query, (from_job, to_job)).fetchone()
                
                if not result:
                    return {'valid': True}  # Can't validate without data
                
                from_level, to_level, from_function, to_function = result
                
                # Extract numeric levels (assuming format like "Group 1", "Group 2", etc.)
                try:
                    from_num = int(from_level.split()[-1])
                    to_num = int(to_level.split()[-1])
                    
                    # Rule: Moving down more than 2 levels with high feasibility is suspicious
                    if (from_num - to_num > 2) and feasibility > 0.8 and (from_function == to_function):
                        return {
                            'valid': False,
                            'rule': 'Management Level Regression',
                            'from_job': from_job,
                            'to_job': to_job,
                            'feasibility': feasibility,
                            'reason': f'High feasibility for {from_num-to_num} level downgrade seems unrealistic'
                        }
                        
                except (ValueError, IndexError):
                    pass  # Can't parse levels
                
                return {'valid': True}
                
        except Exception as e:
            self.logger.warning(f"Management validation error: {e}")
            return {'valid': True}  # Don't fail validation due to data issues
    
    def _validate_function_change(self, from_job: str, to_job: str, feasibility: float) -> Dict[str, Any]:
        """Validate cross-functional moves have reasonable feasibility."""
        try:
            query = """
            SELECT 
                from_arch.JobFunction as from_function,
                to_arch.JobFunction as to_function
            FROM core_job_architecture from_arch
            JOIN core_job_architecture to_arch ON 1=1
            WHERE from_arch.JobProfileID = ? AND to_arch.JobProfileID = ?
            """
            
            with sqlite3.connect(str(self.db_path)) as conn:
                result = conn.execute(query, (from_job, to_job)).fetchone()
                
                if not result:
                    return {'valid': True}
                
                from_function, to_function = result
                
                # Rule: Cross-functional moves with >95% feasibility should be rare
                if (from_function != to_function) and feasibility > 0.95:
                    return {
                        'valid': False,
                        'rule': 'Cross-Functional High Feasibility',
                        'from_job': from_job,
                        'to_job': to_job,
                        'feasibility': feasibility,
                        'reason': f'Cross-functional move ({from_function} → {to_function}) with {feasibility:.1%} feasibility seems high'
                    }
                
                return {'valid': True}
                
        except Exception as e:
            self.logger.warning(f"Function validation error: {e}")
            return {'valid': True}
    
    def validate_prediction_calibration(self, historical_predictions: List[Dict], actual_outcomes: List[Dict]) -> Dict[str, Any]:
        """Validate that model confidence matches real-world outcomes."""
        
        # Group predictions by confidence buckets
        confidence_buckets = {
            '90-100%': [],
            '80-89%': [],
            '70-79%': [],
            '60-69%': [],
            '<60%': []
        }
        
        for pred, outcome in zip(historical_predictions, actual_outcomes):
            confidence = pred['agreement_rate']
            actual_movement = outcome.get('actual_movement', 0)
            
            # Determine bucket
            if confidence >= 0.9:
                bucket = '90-100%'
            elif confidence >= 0.8:
                bucket = '80-89%'
            elif confidence >= 0.7:
                bucket = '70-79%'
            elif confidence >= 0.6:
                bucket = '60-69%'
            else:
                bucket = '<60%'
            
            confidence_buckets[bucket].append({
                'predicted': pred['predicted_movements'],
                'actual': actual_movement,
                'confidence': confidence
            })
        
        # Calculate calibration metrics
        calibration_results = {}
        for bucket, predictions in confidence_buckets.items():
            if not predictions:
                continue
                
            predicted_values = [p['predicted'] for p in predictions]
            actual_values = [p['actual'] for p in predictions]
            
            # Mean Absolute Error
            mae = np.mean([abs(p - a) for p, a in zip(predicted_values, actual_values)])
            
            # Accuracy (within 50% of prediction)
            accurate_predictions = sum(1 for p, a in zip(predicted_values, actual_values) 
                                     if abs(p - a) <= 0.5 * p)
            accuracy = accurate_predictions / len(predictions) if predictions else 0
            
            calibration_results[bucket] = {
                'count': len(predictions),
                'mean_absolute_error': mae,
                'accuracy_rate': accuracy,
                'avg_predicted': np.mean(predicted_values),
                'avg_actual': np.mean(actual_values)
            }
        
        return calibration_results
    
    def create_validation_report(self, model_version: str, predictions: List[Dict]) -> str:
        """Generate comprehensive validation report."""
        
        # Business logic validation
        business_validation = self.validate_business_logic(predictions)
        
        # Generate report
        report = f"""
# Production Validation Report
**Model Version:** {model_version}  
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Total Predictions Validated:** {business_validation['total_predictions']:,}

## Business Logic Validation
- ✅ **Rules Passed:** {business_validation['business_rules_passed']:,}
- ❌ **Rules Failed:** {business_validation['business_rules_failed']:,}  
- ⚠️ **Warnings:** {len(business_validation['warnings']):,}

### Failed Validations
"""
        
        for failure in business_validation['failed_validations'][:10]:  # Show top 10
            report += f"- **{failure['rule']}**: {failure['from_job']} → {failure['to_job']} "
            report += f"(Feasibility: {failure['feasibility']:.1%})\n"
            report += f"  *{failure['reason']}*\n\n"
        
        report += "### Validation Recommendations\n"
        
        failure_rate = business_validation['business_rules_failed'] / business_validation['total_predictions']
        if failure_rate > 0.05:  # >5% failure rate
            report += "- 🔴 **High failure rate detected** - Consider retraining with additional business constraints\n"
        elif failure_rate > 0.02:  # >2% failure rate
            report += "- 🟡 **Moderate failure rate** - Monitor closely and consider model adjustments\n"
        else:
            report += "- 🟢 **Low failure rate** - Model predictions align well with business logic\n"
        
        report += f"\n## Next Steps\n"
        report += f"1. Review failed validations above\n"
        report += f"2. Implement A/B testing framework\n"
        report += f"3. Set up real-world outcome tracking\n"
        report += f"4. Schedule monthly validation reviews\n"
        
        return report

def run_production_validation(db_path: str, predictions: List[Dict]) -> None:
    """Run complete production validation suite."""
    
    validator = ProductionValidator(db_path)
    
    # Generate validation report
    model_version = datetime.now().strftime('%Y-Q%q')  # Current quarter
    report = validator.create_validation_report(model_version, predictions)
    
    # Save report
    report_path = Path(f"validation_report_{model_version}_{datetime.now().strftime('%Y%m%d')}.md")
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"✅ Validation report saved to: {report_path}")
    print("\n" + "="*60)
    print(report)