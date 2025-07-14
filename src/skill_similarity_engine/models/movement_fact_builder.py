"""
Movement Fact Table Builder

This module ports PTH's FactTableBuilder logic to generate position-month 
aggregations for the movement_fact table, enabling strategic workforce planning
and career pathway analysis.

Based on PTH's proven fact table generation patterns.
"""

import logging
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict

from ..config.architectural_config_manager import ArchitecturalConfigManager

logger = logging.getLogger(__name__)


class MovementFactBuilder:
    """
    Builds movement fact tables from individual movement records.
    
    Ports PTH's FactTableBuilder logic to create position-month aggregations
    that enable career pathway analysis and strategic workforce planning.
    """
    
    def __init__(self, config_manager: ArchitecturalConfigManager):
        """
        Initialize the movement fact builder.
        
        Args:
            config_manager: Configuration manager for accessing settings
        """
        self.config = config_manager
        self.fact_table_config = self.config.get_models_movement_analysis_config()
        
        # Configuration settings
        self.aggregation_level = self.fact_table_config.get('aggregation_level', 'monthly')
        self.include_percentages = self.fact_table_config.get('include_percentages', True)
        self.include_tenure_metrics = self.fact_table_config.get('include_tenure_metrics', True)
        
        # Results storage
        self.fact_table_records: List[Dict[str, Any]] = []
        
        logger.info(f"Initialized MovementFactBuilder with aggregation level: {self.aggregation_level}")
    
    def build_fact_table_from_movements(self, movements_df: pd.DataFrame) -> pd.DataFrame:
        """
        Build movement fact table from individual movement records.
        
        This method implements PTH's exact aggregation logic:
        - Groups by Movement_Month + From_Position + To_Position
        - Calculates movement counts, percentages, and tenure statistics
        - Uses Position Number aggregation (not PosIDLookupKey)
        
        Args:
            movements_df: DataFrame containing individual movement records
            
        Returns:
            DataFrame with movement fact table records
        """
        logger.info(f"Building movement fact table from {len(movements_df):,} movement records")
        
        if len(movements_df) == 0:
            logger.warning("No movement records provided for fact table generation")
            return pd.DataFrame()
        
        # Validate required columns
        required_columns = ['employee_number', 'from_position', 'to_position', 'from_date', 'to_date']
        missing_columns = [col for col in required_columns if col not in movements_df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns for fact table generation: {missing_columns}")
        
        # Group movements by pattern and month (PTH's exact logic)
        pattern_stats = defaultdict(lambda: defaultdict(list))
        processed_count = 0
        error_count = 0
        
        for _, movement in movements_df.iterrows():
            try:
                # Extract month and year from movement date
                movement_date = pd.to_datetime(movement['to_date'])
                month_key = movement_date.strftime("%Y-%m")
                
                # Create movement pattern key (from_position -> to_position)
                # Using Position Number aggregation (not PosIDLookupKey)
                pattern_key = (str(movement['from_position']), str(movement['to_position']))
                
                # Calculate days between positions
                days_between = self._calculate_days_between(movement['from_date'], movement['to_date'])
                
                # Store movement details for aggregation
                pattern_stats[month_key][pattern_key].append({
                    'employee_number': movement['employee_number'],
                    'days_between': days_between,
                    'movement_type': movement.get('movement_type', 'lateral'),
                    'duration_days': movement.get('duration_days', days_between)
                })
                
                processed_count += 1
                
            except Exception as e:
                error_count += 1
                if error_count <= 5:  # Only show first 5 errors
                    logger.warning(f"Error processing movement: {e}")
                continue
        
        logger.info(f"Processed {processed_count:,} movements, {error_count:,} errors")
        logger.info(f"Found {len(pattern_stats)} months with movement patterns")
        
        # Convert to fact table records (PTH's exact structure)
        fact_records = []
        
        for month, patterns in pattern_stats.items():
            year = int(month[:4])
            
            # Calculate monthly total movements
            monthly_total = sum(len(movements) for movements in patterns.values())
            
            # Create fact table rows for each movement pattern
            for pattern, movements in patterns.items():
                from_position, to_position = pattern
                movement_count = len(movements)
                
                # Calculate aggregated metrics
                unique_employees = len(set(m['employee_number'] for m in movements))
                avg_days_between = sum(m['days_between'] for m in movements) / movement_count
                
                # Calculate percentage of total movements
                pct_total_movements = (movement_count / monthly_total * 100) if monthly_total > 0 else 0
                
                # Create fact table record
                fact_record = {
                    'Movement_Month': month,
                    'Movement_Year': year,
                    'From_Position': from_position,
                    'To_Position': to_position,
                    'Movement_Pattern': f"{from_position} → {to_position}",
                    'Movement_Count': movement_count,
                    'Unique_Employees': unique_employees,
                    'Monthly_Total_Movements': monthly_total
                }
                
                # Add percentage metrics if configured
                if self.include_percentages:
                    fact_record['Pct_Total_Movements'] = round(pct_total_movements, 2)
                
                # Add tenure metrics if configured
                if self.include_tenure_metrics:
                    fact_record['Avg_Days_Between'] = round(avg_days_between, 1)
                    fact_record['Min_Days_Between'] = min(m['days_between'] for m in movements)
                    fact_record['Max_Days_Between'] = max(m['days_between'] for m in movements)
                
                fact_records.append(fact_record)
        
        # Convert to DataFrame
        fact_table_df = pd.DataFrame(fact_records)
        
        # Sort by month and movement count (descending)
        if len(fact_table_df) > 0:
            fact_table_df = fact_table_df.sort_values(['Movement_Month', 'Movement_Count'], 
                                                     ascending=[True, False])
        
        logger.info(f"Generated {len(fact_table_df):,} movement fact table records")
        
        # Store for later access
        self.fact_table_records = fact_records
        
        return fact_table_df
    
    def _calculate_days_between(self, from_date: str, to_date: str) -> int:
        """
        Calculate days between two dates.
        
        Args:
            from_date: Start date (string)
            to_date: End date (string)
            
        Returns:
            Number of days between dates
        """
        try:
            from_dt = pd.to_datetime(from_date)
            to_dt = pd.to_datetime(to_date)
            delta = to_dt - from_dt
            return max(0, delta.days)  # Ensure non-negative
        except Exception as e:
            logger.warning(f"Error calculating days between {from_date} and {to_date}: {e}")
            return 0
    
    def get_fact_table_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics of the generated fact table.
        
        Returns:
            Dictionary with fact table summary statistics
        """
        if not self.fact_table_records:
            return {
                'total_movements': 0,
                'unique_patterns': 0,
                'unique_months': 0,
                'avg_movements_per_pattern': 0
            }
        
        total_movements = sum(record['Movement_Count'] for record in self.fact_table_records)
        unique_patterns = len(self.fact_table_records)
        unique_months = len(set(record['Movement_Month'] for record in self.fact_table_records))
        avg_movements_per_pattern = total_movements / unique_patterns if unique_patterns > 0 else 0
        
        return {
            'total_movements': total_movements,
            'unique_patterns': unique_patterns,
            'unique_months': unique_months,
            'avg_movements_per_pattern': round(avg_movements_per_pattern, 1)
        }
    
    def export_fact_table(self, output_path: str) -> None:
        """
        Export the fact table to CSV file.
        
        Args:
            output_path: Path to save the fact table CSV
        """
        if not self.fact_table_records:
            logger.warning("No fact table data to export")
            return
        
        fact_table_df = pd.DataFrame(self.fact_table_records)
        fact_table_df.to_csv(output_path, index=False)
        
        logger.info(f"Exported fact table to {output_path}")
        logger.info(f"Exported {len(fact_table_df):,} fact table records") 