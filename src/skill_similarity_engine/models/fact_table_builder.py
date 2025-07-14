"""
Fact Table Builder for Movement Analysis

This module handles the creation and export of the movement fact table
for Power BI analysis and database integration. It aggregates individual 
movements into patterns and calculates key metrics.

Ported from position_transition_history to skill-similarity-engine with
enhanced SSE integration capabilities.
"""

import csv
import logging
from typing import Dict, List, Tuple, Any
from collections import defaultdict
from datetime import datetime
import pandas as pd

from .movement_tracker import MovementTracker

logger = logging.getLogger(__name__)


class FactTableBuilder:
    """Builds the movement fact table for Power BI analysis and database integration."""
    
    def __init__(self, movement_tracker: MovementTracker):
        """
        Initialize the fact table builder.
        
        Args:
            movement_tracker: MovementTracker with detected movements
        """
        self.movement_tracker = movement_tracker
        self.fact_table: List[Dict[str, Any]] = []
        
    def build_fact_table(self) -> None:
        """Build the movement fact table from detected movements."""
        logger.info("📊 Building movement fact table...")
        
        if not self.movement_tracker.movement_events:
            logger.warning("❌ No movement events found to process!")
            return
        
        # Debug: Check sample movement events
        sample_movements = self.movement_tracker.movement_events[:3]
        logger.info(f"🔍 Debug: First 3 movements:")
        for i, movement in enumerate(sample_movements):
            logger.info(f"  {i+1}. Employee {movement.employee_number}: {movement.from_position} → {movement.to_position}")
            logger.info(f"     From: '{movement.from_date}' To: '{movement.to_date}'")
        
        # Group movements by pattern and month
        pattern_stats = defaultdict(lambda: defaultdict(list))
        processed_count = 0
        error_count = 0
        
        for movement in self.movement_tracker.movement_events:
            try:
                # Extract month and year
                movement_date = datetime.strptime(movement.to_date, "%Y-%m-%d")
                month_key = movement_date.strftime("%Y-%m")
                pattern_key = (movement.from_position, movement.to_position)
                
                # Store movement details
                pattern_stats[month_key][pattern_key].append({
                    'employee_number': movement.employee_number,
                    'days_between': self._calculate_days_between(movement.from_date, movement.to_date),
                    'movement_type': getattr(movement, 'movement_type', 'lateral')
                })
                processed_count += 1
                
            except Exception as e:
                error_count += 1
                if error_count <= 5:  # Only show first 5 errors
                    logger.warning(f"  ⚠️ Error processing movement: {e}")
                    logger.warning(f"     Movement: {movement}")
        
        logger.info(f"📊 Processed {processed_count:,} movements, {error_count:,} errors")
        logger.info(f"📅 Found {len(pattern_stats)} months with movements")
        
        # Convert to fact table rows
        for month, patterns in pattern_stats.items():
            year = int(month[:4])
            
            # Calculate monthly total
            monthly_total = sum(len(movements) for movements in patterns.values())
            
            # Create fact table rows
            for pattern, movements in patterns.items():
                from_position, to_position = pattern
                movement_count = len(movements)
                
                # Calculate additional metrics
                unique_employees = len(set(m['employee_number'] for m in movements))
                avg_days_between = round(sum(m['days_between'] for m in movements) / movement_count, 1) if movement_count > 0 else 0
                pct_total_movements = round(movement_count / monthly_total * 100, 2) if monthly_total > 0 else 0
                
                # Determine predominant movement type
                movement_types = [m['movement_type'] for m in movements]
                predominant_type = max(set(movement_types), key=movement_types.count) if movement_types else 'lateral'
                
                self.fact_table.append({
                    'Movement_Month': month,
                    'Movement_Year': year,
                    'From_Position': from_position,
                    'To_Position': to_position,
                    'Movement_Pattern': f"{from_position} → {to_position}",
                    'Movement_Count': movement_count,
                    'Pct_Total_Movements': pct_total_movements,
                    'Unique_Employees': unique_employees,
                    'Avg_Days_Between': avg_days_between,
                    'Monthly_Total_Movements': monthly_total,
                    'Predominant_Movement_Type': predominant_type
                })
        
        logger.info(f"✅ Built fact table with {len(self.fact_table):,} movement patterns")
    
    def _calculate_days_between(self, from_date: str, to_date: str) -> int:
        """Calculate days between two dates."""
        try:
            from_dt = datetime.strptime(from_date, "%Y-%m-%d")
            to_dt = datetime.strptime(to_date, "%Y-%m-%d")
            return abs((to_dt - from_dt).days)
        except (ValueError, AttributeError):
            return 0
    
    def export_fact_table_to_csv(self, output_path: str) -> None:
        """
        Export the fact table to CSV.
        
        Args:
            output_path: Path to save the fact table CSV
        """
        if not self.fact_table:
            logger.warning("⚠️ No fact table data to export!")
            return
        
        with open(output_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=list(self.fact_table[0].keys()))
            writer.writeheader()
            writer.writerows(self.fact_table)
        
        logger.info(f"💾 Exported fact table to {output_path}")
    
    def export_fact_table_to_parquet(self, output_path: str) -> None:
        """
        Export the fact table to Parquet format.
        
        Args:
            output_path: Path to save the fact table Parquet file
        """
        if not self.fact_table:
            logger.warning("⚠️ No fact table data to export!")
            return
        
        df = pd.DataFrame(self.fact_table)
        df.to_parquet(output_path, index=False, compression='snappy')
        
        logger.info(f"💾 Exported fact table to {output_path}")
    
    def get_fact_table_dataframe(self) -> pd.DataFrame:
        """
        Get the fact table as a pandas DataFrame.
        
        Returns:
            DataFrame containing the fact table data
        """
        if not self.fact_table:
            return pd.DataFrame()
        
        return pd.DataFrame(self.fact_table)
    
    def get_summary_stats(self) -> Dict[str, int]:
        """Get summary statistics of the fact table."""
        if not self.fact_table:
            return {
                'total_movements': 0,
                'unique_patterns': 0,
                'unique_months': 0,
                'unique_positions': 0
            }
        
        total_movements = sum(row['Movement_Count'] for row in self.fact_table)
        unique_patterns = len(self.fact_table)
        unique_months = len(set(row['Movement_Month'] for row in self.fact_table))
        
        # Get unique positions involved
        positions = set()
        for row in self.fact_table:
            positions.add(row['From_Position'])
            positions.add(row['To_Position'])
        unique_positions = len(positions)
        
        return {
            'total_movements': total_movements,
            'unique_patterns': unique_patterns,
            'unique_months': unique_months,
            'unique_positions': unique_positions
        }
    
    def get_top_movement_patterns(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Get the top N movement patterns by count.
        
        Args:
            top_n: Number of top patterns to return
            
        Returns:
            List of top movement patterns
        """
        if not self.fact_table:
            return []
        
        # Sort by movement count descending
        sorted_patterns = sorted(self.fact_table, key=lambda x: x['Movement_Count'], reverse=True)
        return sorted_patterns[:top_n]
    
    def get_monthly_movement_summary(self) -> Dict[str, Dict[str, int]]:
        """
        Get monthly movement summary statistics.
        
        Returns:
            Dictionary with monthly movement statistics
        """
        if not self.fact_table:
            return {}
        
        monthly_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: {
            'total_movements': 0,
            'unique_patterns': 0
        })
        
        for row in self.fact_table:
            month = row['Movement_Month']
            monthly_stats[month]['total_movements'] += row['Movement_Count']
            monthly_stats[month]['unique_patterns'] += 1
        
        return dict(monthly_stats) 