"""
Database Integrator for Direct Analytics Table Population

This module provides consistent database integration for all analytics phases,
eliminating intermediate files and enabling direct database population as
specified in the NEXT_PHASE_IMPLEMENTATION_GUIDE.md.
"""

import logging
import sqlite3
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
from datetime import datetime

from ..config.architectural_config_manager import get_config_manager
from ..error_handling.recovery import retry, circuit_breaker, fallback_on_failure


class DatabaseIntegrator:
    """
    Handles direct database integration for analytics phases.
    
    This class provides consistent database integration for all analytics phases
    (Phase 1, 2, 3) with proper error handling, transaction management, and
    metadata tracking.
    """
    
    def __init__(self, db_path: Path):
        """
        Initialize the database integrator.
        
        Args:
            db_path: Path to the SQLite database
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.config_manager = get_config_manager()
        
        self.logger.info(f"Database integrator initialized with database: {db_path}")
    
    @retry(max_attempts=3)
    @circuit_breaker(failure_threshold=3)
    def populate_job_similarities(self, similarities_df: pd.DataFrame) -> bool:
        """
        Populate analytics_job_similarities table.
        
        Args:
            similarities_df: DataFrame with enhanced similarity data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            print(f"   📊 Saving {len(similarities_df):,} job similarity records...")
            
            with sqlite3.connect(self.db_path) as conn:
                # Clear existing data
                conn.execute("DELETE FROM analytics_job_similarities")
                # Cleared existing data for fresh analytics
                
                # Insert new data
                similarities_df.to_sql('analytics_job_similarities', conn, if_exists='append', index=False)
                
                # Update metadata
                self._update_table_metadata(conn, 'analytics_job_similarities', len(similarities_df))
                
                self.logger.info(f"Successfully populated analytics_job_similarities with {len(similarities_df):,} records")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to populate job similarities: {e}", exc_info=True)
            return False
    
    @retry(max_attempts=3)
    @circuit_breaker(failure_threshold=3)
    def populate_skill_rarity(self, rarity_df: pd.DataFrame) -> bool:
        """
        Populate analytics_skill_rarity table.
        
        Args:
            rarity_df: DataFrame with skill rarity analysis data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Populating skill rarity table with {len(rarity_df):,} records")
            
            with sqlite3.connect(self.db_path) as conn:
                # Clear existing data
                conn.execute("DELETE FROM analytics_skill_rarity")
                # Cleared existing data for fresh analytics
                
                # Insert new data
                rarity_df.to_sql('analytics_skill_rarity', conn, if_exists='append', index=False)
                
                # Update metadata
                self._update_table_metadata(conn, 'analytics_skill_rarity', len(rarity_df))
                
                self.logger.info(f"Successfully populated analytics_skill_rarity with {len(rarity_df):,} records")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to populate skill rarity: {e}", exc_info=True)
            return False
    
    @retry(max_attempts=3)
    @circuit_breaker(failure_threshold=3)
    def populate_job_defining_skills(self, defining_skills_df: pd.DataFrame) -> bool:
        """
        Populate analytics_job_defining_skills table.
        
        Args:
            defining_skills_df: DataFrame with job defining skills data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Populating job defining skills table with {len(defining_skills_df):,} records")
            
            with sqlite3.connect(self.db_path) as conn:
                # Clear existing data
                conn.execute("DELETE FROM analytics_job_defining_skills")
                # Cleared existing data for fresh analytics
                
                # Insert new data
                defining_skills_df.to_sql('analytics_job_defining_skills', conn, if_exists='append', index=False)
                
                # Update metadata
                self._update_table_metadata(conn, 'analytics_job_defining_skills', len(defining_skills_df))
                
                self.logger.info(f"Successfully populated analytics_job_defining_skills with {len(defining_skills_df):,} records")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to populate job defining skills: {e}", exc_info=True)
            return False
    
    @retry(max_attempts=3)
    @circuit_breaker(failure_threshold=3)
    def populate_movement_patterns(self, movement_df: pd.DataFrame) -> bool:
        """
        Populate analytics_movement_patterns table.
        
        Args:
            movement_df: DataFrame with movement patterns data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Populating movement patterns table with {len(movement_df):,} records")
            
            # Fail fast if no movement patterns generated
            if len(movement_df) == 0:
                raise ValueError("No movement patterns provided - fact table generation failed")
            
            # Fail fast if required column missing
            if 'movement_pattern_id' not in movement_df.columns:
                raise ValueError(f"Required column 'movement_pattern_id' missing from DataFrame. Available columns: {list(movement_df.columns)}")
            
            with sqlite3.connect(self.db_path) as conn:
                # Clear existing data
                conn.execute("DELETE FROM analytics_movement_patterns")
                conn.commit()  # Ensure deletion is committed before insertion
                # Cleared existing data for fresh analytics
                
                # Validate movement pattern IDs
                duplicate_ids = movement_df['movement_pattern_id'].duplicated().sum()
                if duplicate_ids > 0:
                    self.logger.warning(f"Found {duplicate_ids} duplicate movement_pattern_id values in DataFrame!")
                    raise ValueError(f"Duplicate movement_pattern_id values detected: {duplicate_ids} duplicates")
                
                # Insert new data
                movement_df.to_sql('analytics_movement_patterns', conn, if_exists='append', index=False)
                
                # Update metadata
                self._update_table_metadata(conn, 'analytics_movement_patterns', len(movement_df))
                
                self.logger.info(f"Successfully populated analytics_movement_patterns with {len(movement_df):,} records")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to populate movement patterns: {e}", exc_info=True)
            return False
    
    @retry(max_attempts=3)
    @circuit_breaker(failure_threshold=3)
    def populate_pathway_predictions(self, predictions_df: pd.DataFrame) -> bool:
        """
        Populate analytics_pathway_predictions table with ML predictions.
        
        Args:
            predictions_df: DataFrame with ML pathway predictions
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Populating pathway predictions table with {len(predictions_df):,} records")
            
            with sqlite3.connect(self.db_path) as conn:
                # Clear existing data
                conn.execute("DELETE FROM analytics_pathway_predictions")
                conn.commit()  # Ensure deletion is committed before insertion
                # Cleared existing data for fresh analytics
                
                # Validate prediction IDs
                duplicate_ids = predictions_df['prediction_id'].duplicated().sum()
                if duplicate_ids > 0:
                    self.logger.warning(f"Found {duplicate_ids} duplicate prediction_id values in DataFrame!")
                    raise ValueError(f"Duplicate prediction_id values detected: {duplicate_ids} duplicates")
                
                # Insert new data
                predictions_df.to_sql('analytics_pathway_predictions', conn, if_exists='append', index=False)
                
                # Update metadata
                self._update_table_metadata(conn, 'analytics_pathway_predictions', len(predictions_df))
                
                self.logger.info(f"Successfully populated analytics_pathway_predictions with {len(predictions_df):,} records")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to populate pathway predictions: {e}", exc_info=True)
            return False
    
    @retry(max_attempts=3)
    @circuit_breaker(failure_threshold=3)
    def populate_job_families(self, job_families_df: pd.DataFrame) -> bool:
        """
        Populate analytics_job_families table.
        
        Args:
            job_families_df: DataFrame with job families (clustering) data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Populating job families table with {len(job_families_df):,} records")
            
            with sqlite3.connect(self.db_path) as conn:
                # Clear existing data
                conn.execute("DELETE FROM analytics_job_families")
                # Cleared existing data for fresh analytics
                
                # Insert new data
                job_families_df.to_sql('analytics_job_families', conn, if_exists='append', index=False)
                
                # Update metadata
                self._update_table_metadata(conn, 'analytics_job_families', len(job_families_df))
                
                self.logger.info(f"Successfully populated analytics_job_families with {len(job_families_df):,} records")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to populate job families: {e}", exc_info=True)
            return False
    
    @retry(max_attempts=3)
    @circuit_breaker(failure_threshold=3)
    def populate_skill_bundles(self, skill_bundles_df: pd.DataFrame) -> bool:
        """
        Populate analytics_skill_bundles table.
        
        Args:
            skill_bundles_df: DataFrame with skill bundles (clustering) data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Populating skill bundles table with {len(skill_bundles_df):,} records")
            
            with sqlite3.connect(self.db_path) as conn:
                # Clear existing data
                conn.execute("DELETE FROM analytics_skill_bundles")
                # Cleared existing data for fresh analytics
                
                # Insert new data
                skill_bundles_df.to_sql('analytics_skill_bundles', conn, if_exists='append', index=False)
                
                # Update metadata
                self._update_table_metadata(conn, 'analytics_skill_bundles', len(skill_bundles_df))
                
                self.logger.info(f"Successfully populated analytics_skill_bundles with {len(skill_bundles_df):,} records")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to populate skill bundles: {e}", exc_info=True)
            return False
    
    @retry(max_attempts=3)
    @circuit_breaker(failure_threshold=3)
    def populate_skill_demand_trends(self, trends_df: pd.DataFrame) -> bool:
        """
        Populate analytics_skill_demand_trends table.
        
        Args:
            trends_df: DataFrame with skill demand trends (velocity) data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Populating skill demand trends table with {len(trends_df):,} records")
            
            with sqlite3.connect(self.db_path) as conn:
                # Clear existing data
                conn.execute("DELETE FROM analytics_skill_demand_trends")
                # Cleared existing data for fresh analytics
                
                # Insert new data
                trends_df.to_sql('analytics_skill_demand_trends', conn, if_exists='append', index=False)
                
                # Update metadata
                self._update_table_metadata(conn, 'analytics_skill_demand_trends', len(trends_df))
                
                self.logger.info(f"Successfully populated analytics_skill_demand_trends with {len(trends_df):,} records")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to populate skill demand trends: {e}", exc_info=True)
            return False
    
    @retry(max_attempts=3)
    @circuit_breaker(failure_threshold=3)
    def populate_specialized_skills(self, specialized_df: pd.DataFrame) -> bool:
        """
        Populate analytics_specialized_skills table.
        
        Args:
            specialized_df: DataFrame with specialized skills data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Populating specialized skills table with {len(specialized_df):,} records")
            
            with sqlite3.connect(self.db_path) as conn:
                # Clear existing data
                conn.execute("DELETE FROM analytics_specialized_skills")
                # Cleared existing data for fresh analytics
                
                # Insert new data
                specialized_df.to_sql('analytics_specialized_skills', conn, if_exists='append', index=False)
                
                # Update metadata
                self._update_table_metadata(conn, 'analytics_specialized_skills', len(specialized_df))
                
                self.logger.info(f"Successfully populated analytics_specialized_skills with {len(specialized_df):,} records")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to populate specialized skills: {e}", exc_info=True)
            return False
    
    @retry(max_attempts=3)
    @circuit_breaker(failure_threshold=3)
    def populate_bundle_characteristics(self, characteristics_df: pd.DataFrame) -> bool:
        """
        Populate analytics_bundle_characteristics table.
        
        Args:
            characteristics_df: DataFrame with bundle characteristics data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Populating bundle characteristics table with {len(characteristics_df):,} records")
            
            with sqlite3.connect(self.db_path) as conn:
                # Clear existing data
                conn.execute("DELETE FROM analytics_bundle_characteristics")
                # Cleared existing data for fresh analytics
                
                # Insert new data
                characteristics_df.to_sql('analytics_bundle_characteristics', conn, if_exists='append', index=False)
                
                # Update metadata
                self._update_table_metadata(conn, 'analytics_bundle_characteristics', len(characteristics_df))
                
                self.logger.info(f"Successfully populated analytics_bundle_characteristics with {len(characteristics_df):,} records")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to populate bundle characteristics: {e}", exc_info=True)
            return False
    
    def verify_table_populated(self, table_name: str) -> bool:
        """
        Verify that a table has been populated with data.
        
        Args:
            table_name: Name of the table to check
            
        Returns:
            True if table has data, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                return count > 0
                
        except Exception as e:
            self.logger.error(f"Failed to verify table {table_name}: {e}")
            return False
    
    def get_table_record_count(self, table_name: str) -> int:
        """
        Get the number of records in a table.
        
        Args:
            table_name: Name of the table to check
            
        Returns:
            Number of records in the table, or 0 if error
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
                return cursor.fetchone()[0]
                
        except Exception as e:
            self.logger.error(f"Failed to get record count for {table_name}: {e}")
            return 0
    
    def get_analytics_summary(self) -> Dict[str, int]:
        """
        Get a summary of all analytics tables and their record counts.
        
        Returns:
            Dictionary mapping table names to record counts
        """
        analytics_tables = [
            'analytics_job_similarities',
            'analytics_skill_rarity', 
            'analytics_job_defining_skills',
            'analytics_movement_patterns',
            'analytics_job_families',
            'analytics_skill_bundles',
            'analytics_skill_demand_trends',
            'analytics_specialized_skills',
            'analytics_bundle_characteristics'
        ]
        
        summary = {}
        for table in analytics_tables:
            summary[table] = self.get_table_record_count(table)
        
        return summary
    
    def clear_analytics_data(self, phase: Optional[str] = None) -> bool:
        """
        Clear analytics data for a specific phase or all phases.
        
        Args:
            phase: Phase to clear ('phase_1', 'phase_2', 'phase_3') or None for all
            
        Returns:
            True if successful, False otherwise
        """
        try:
            phase_table_mapping = {
                'phase_1': [
                    'analytics_job_similarities',
                    'analytics_skill_rarity',
                    'analytics_job_defining_skills'
                ],
                'phase_2': [
                    'analytics_movement_patterns'
                ],
                'phase_3': [
                    'analytics_job_families',
                    'analytics_skill_bundles',
                    'analytics_skill_demand_trends',
                    'analytics_specialized_skills',
                    'analytics_bundle_characteristics'
                ]
            }
            
            if phase:
                tables_to_clear = phase_table_mapping.get(phase, [])
            else:
                # Clear all analytics tables
                tables_to_clear = []
                for tables in phase_table_mapping.values():
                    tables_to_clear.extend(tables)
            
            with sqlite3.connect(self.db_path) as conn:
                for table in tables_to_clear:
                    conn.execute(f"DELETE FROM {table}")
                    self.logger.info(f"Cleared {table}")
                
                # Update metadata
                for table in tables_to_clear:
                    self._update_table_metadata(conn, table, 0)
            
            print(f"🧹 Cleared analytics data for {phase or 'all phases'}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to clear analytics data: {e}")
            print("   Check database connectivity and permissions.")
            return False
    
    def _update_table_metadata(self, conn: sqlite3.Connection, table_name: str, record_count: int):
        """
        Update sys_schema_metadata with table population info.
        
        Args:
            conn: Database connection
            table_name: Name of the table
            record_count: Number of records in the table
        """
        try:
            # Insert metadata using the correct schema
            metadata_key = f"table_{table_name}_record_count"
            metadata_value = str(record_count)
            current_time = datetime.now().isoformat()
            
            conn.execute("""
                INSERT OR REPLACE INTO sys_schema_metadata 
                (metadata_key, metadata_value, metadata_category, description, updated_timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (
                metadata_key,
                metadata_value,
                "table_stats",
                f"Record count for {table_name} table",
                current_time
            ))
            
        except Exception as e:
            print(f"⚠️ Failed to update metadata for {table_name}: {e}")
    
    @fallback_on_failure(default=False)
    def test_database_connectivity(self) -> bool:
        """
        Test database connectivity and basic functionality.
        
        Returns:
            True if database is accessible, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Test basic query
                cursor = conn.execute("SELECT COUNT(*) FROM sqlite_master")
                cursor.fetchone()
                return True
                
        except Exception as e:
            self.logger.error(f"Database connectivity test failed: {e}")
            return False