"""
Data Loading Pipeline for Business Context Database

Handles loading CSV data from multiple directories into SQLite tables:
- Job architecture data
- Skills library data  
- Workforce context data
- Job-skill mapping data

Provides progress tracking, data validation, and error handling.
Uses YAML configuration for data source definitions and mappings.
"""

import logging
import sqlite3
import pandas as pd
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

logger = logging.getLogger(__name__)


class DataLoader:
    """Loads CSV data into SQLite business context database."""
    
    def __init__(self, db_path: str, config_path: str = "config/data_sources.yaml"):
        """
        Initialize data loader.
        
        Args:
            db_path: Path to SQLite database file
            config_path: Path to YAML configuration file
        """
        self.db_path = Path(db_path)
        self.config_path = Path(config_path)
        self.load_stats = {}
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                logger.info(f"Loaded data sources configuration from {self.config_path}")
                return config
            else:
                logger.warning(f"Configuration file not found: {self.config_path}")
                return self._get_default_config()
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration when YAML file is not available."""
        return {
            'data_sources': {
                'jobs': {
                    'file_path': 'job_architecture/dummy_job_architecture.csv',
                    'column_mapping': {
                        'JobProfileID': 'JobProfileID',
                        'JobProfile': 'JobProfile',
                        'JobID': 'JobID',
                        'Job': 'Job',
                        'JobFamily': 'JobFamily',
                        'JobFamilyGroup': 'JobFamilyGroup'
                    }
                },
                'skills': {
                    'file_path': 'skills_library/lightcast_skills_comprehensive.csv',
                    'column_mapping': {
                        'skill_id': 'Skill_ID',
                        'name': 'Skill_Name',
                        'category': 'Category',
                        'subcategory': 'Subcategory',
                        'type': 'SkillType',
                        'latest_version': 'Latest_Version'
                    },
                    'chunk_size': 10000
                },
                'job_skills': {
                    'file_path': 'input_data/job_skill_mapping.csv',
                    'column_mapping': {
                        'JobProfileID': 'JobProfileID',
                        'Skill_Name': 'Skill_Name',
                        'Skill_ID': 'Skill_ID'
                    }
                },
                'positions': {
                    'file_path': 'workforce_context/dummy_workforce_context.csv',
                    'column_mapping': {
                        'Position Number': 'Position_Number',
                        'JobProfileID': 'JobProfileID',
                        'Employee Number': 'Employee_Number',
                        'Business Unit': 'Business_Unit',
                        'ORG_UNIT_NAME_1': 'Department',
                        'ORG_UNIT_NAME_2': 'Team',
                        'Location': 'Location',
                        'State/Territory': 'State',
                        'Country': 'Country',
                        'Employment Type': 'Employment_Type',
                        'Salary Group': 'Salary_Grade',
                        'Work Pattern': 'Work_Pattern'
                    }
                }
            },
            'loading': {'default_chunk_size': 1000}
        }
        
    def load_all_data(self, data_root: str = "data") -> bool:
        """
        Load all CSV data sources into the database using configuration.
        
        Args:
            data_root: Root directory containing data subdirectories
            
        Returns:
            True if all data loaded successfully
        """
        data_root_path = Path(data_root)
        success = True
        
        logger.info("Starting comprehensive data loading from configuration...")
        
        # Get data sources from configuration
        data_sources = self.config.get('data_sources', {})
        
        # Define loading sequence (order matters for foreign keys)
        loading_sequence = ['jobs', 'skills', 'job_skills', 'positions']
        
        for dataset_name in loading_sequence:
            if dataset_name not in data_sources:
                logger.warning(f"Dataset {dataset_name} not found in configuration")
                continue
                
            dataset_config = data_sources[dataset_name]
            file_path = data_root_path / dataset_config['file_path']
            
            if file_path.exists():
                logger.info(f"Loading {dataset_name} from {file_path}")
                if not self._load_dataset_from_config(dataset_name, file_path, dataset_config):
                    logger.error(f"Failed to load {dataset_name}")
                    success = False
                else:
                    logger.info(f"✓ Successfully loaded {dataset_name}")
            else:
                logger.warning(f"Data file not found: {file_path}")
                success = False
        
        if success:
            logger.info("All data loaded successfully")
            self._print_load_summary()
        
        return success
    
    def _load_dataset_from_config(self, dataset_name: str, file_path: Path, dataset_config: Dict[str, Any]) -> bool:
        """
        Load a dataset using configuration.
        
        Args:
            dataset_name: Name of the dataset (jobs, skills, etc.)
            file_path: Path to CSV file
            dataset_config: Configuration for this dataset
            
        Returns:
            True if loaded successfully
        """
        try:
            logger.info(f"Loading {dataset_name} from {file_path}")
            
            # Read CSV with optional chunk size
            chunk_size = dataset_config.get('chunk_size')
            df = pd.read_csv(file_path, low_memory=False)
            
            # Handle position enrichment if configured
            if dataset_name == 'positions' and dataset_config.get('enrichment', {}).get('enabled', False):
                enrichment_config = dataset_config['enrichment']
                mapping_file_path = file_path.parent.parent / enrichment_config['mapping_file']
                
                if mapping_file_path.exists():
                    logger.info(f"Loading position-job mapping from {mapping_file_path}")
                    df_mapping = pd.read_csv(mapping_file_path)
                    
                    # Merge positions with JobProfileID mapping
                    merge_key = enrichment_config.get('merge_key', 'Position Number')
                    df = df.merge(
                        df_mapping, 
                        left_on=merge_key, 
                        right_on='Position_Number',
                        how='left'
                    )
                    
                    # Log enrichment statistics
                    positions_with_jobs = df['JobProfileID'].notna().sum()
                    total_positions = len(df)
                    enrichment_rate = (positions_with_jobs / total_positions * 100) if total_positions > 0 else 0
                    logger.info(f"Position enrichment: {positions_with_jobs:,} of {total_positions:,} positions have JobProfileID ({enrichment_rate:.1f}%)")
                else:
                    logger.warning(f"Position-job mapping file not found: {mapping_file_path}")
                    df['JobProfileID'] = ''
            
            # Get column mapping from configuration
            column_mapping = dataset_config.get('column_mapping', {})
            
            # Select and rename columns based on mapping
            available_columns = [col for col in column_mapping.keys() if col in df.columns]
            if not available_columns:
                logger.error(f"No expected columns found in {file_path}")
                return False
                
            df_mapped = df[available_columns].rename(columns=column_mapping)
            
            # Add default values from configuration (important for skills!)
            default_values = dataset_config.get('default_values', {})
            for col, default_val in default_values.items():
                if col not in df_mapped.columns:
                    df_mapped[col] = default_val
                    logger.info(f"Added default column {col} with value {default_val}")
            
            # Handle derived columns
            derived_columns = dataset_config.get('derived_columns', {})
            for new_col, source_col in derived_columns.items():
                if source_col in df_mapped.columns:
                    df_mapped[new_col] = df_mapped[source_col]
                else:
                    df_mapped[new_col] = ''
            
            # Apply data type conversions
            data_types = dataset_config.get('data_types', {})
            for col, dtype in data_types.items():
                if col in df_mapped.columns:
                    if dtype == 'numeric':
                        df_mapped[col] = pd.to_numeric(df_mapped[col], errors='coerce')
            
            # Clean data
            df_mapped = df_mapped.fillna('')
            
            # Remove rows with empty primary keys if specified
            table_name = dataset_config.get('table_name', dataset_name)
            if dataset_name == 'jobs' and 'JobProfileID' in df_mapped.columns:
                df_mapped = df_mapped[df_mapped['JobProfileID'] != '']
            elif dataset_name == 'positions' and 'Position Number' in df_mapped.columns:
                df_mapped = df_mapped[df_mapped['Position Number'] != '']
            elif dataset_name == 'job_skills':
                df_mapped = df_mapped[df_mapped['JobProfileID'] != '']
                df_mapped = df_mapped[df_mapped['Skill_ID'] != '']
            elif dataset_name == 'skills' and 'Skill_ID' in df_mapped.columns:
                df_mapped = df_mapped[df_mapped['Skill_ID'] != '']
                df_mapped = df_mapped.drop_duplicates(subset=['Skill_ID'])
            
            # Load into database
            with sqlite3.connect(self.db_path) as conn:
                if chunk_size and len(df_mapped) > chunk_size:
                    df_mapped.to_sql(table_name, conn, if_exists='append', index=False, chunksize=chunk_size)
                else:
                    df_mapped.to_sql(table_name, conn, if_exists='append', index=False)
                
                # Get row count for stats
                cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]
            
            # Store enrichment rate in stats if applicable
            enrichment_rate = 0
            if dataset_name == 'positions' and 'enrichment_rate' in locals():
                enrichment_rate = locals()['enrichment_rate']
            
            self.load_stats[dataset_name] = {
                'rows_loaded': len(df_mapped),
                'total_rows': row_count,
                'source_file': str(file_path),
                'enrichment_rate': enrichment_rate
            }
            
            logger.info(f"Loaded {len(df_mapped)} {dataset_name} records")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load {dataset_name}: {e}")
            return False
    
    def _load_job_architecture(self, file_path: Path) -> bool:
        """Load job architecture data into jobs table."""
        try:
            logger.info(f"Loading job architecture from {file_path}")
            
            # Read CSV with proper data types
            df = pd.read_csv(file_path)
            
            # Map columns to database schema
            column_mapping = {
                'JobProfileID': 'JobProfileID',
                'JobProfile': 'JobProfile', 
                'JobID': 'JobID',
                'Job': 'Job',
                'JobFamily': 'JobFamily',
                'JobFamilyGroup': 'JobFamilyGroup'
            }
            
            # Select and rename columns
            df_mapped = df[list(column_mapping.keys())].rename(columns=column_mapping)
            
            # Clean data
            df_mapped = df_mapped.fillna('')  # Replace NaN with empty strings
            
            # Load into database
            with sqlite3.connect(self.db_path) as conn:
                df_mapped.to_sql('jobs', conn, if_exists='append', index=False)
                
                # Get row count for stats
                cursor = conn.execute("SELECT COUNT(*) FROM jobs")
                row_count = cursor.fetchone()[0]
                
            self.load_stats['jobs'] = {
                'rows_loaded': len(df_mapped),
                'total_rows': row_count,
                'source_file': str(file_path)
            }
            
            logger.info(f"Loaded {len(df_mapped)} job records")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load job architecture: {e}")
            return False
    
    def _load_skills_library(self, file_path: Path) -> bool:
        """Load comprehensive skills library into skills table."""
        try:
            logger.info(f"Loading skills library from {file_path}")
            
            # Read CSV - handle large file efficiently
            df = pd.read_csv(file_path, low_memory=False)
            
            # Map columns to database schema
            column_mapping = {
                'skill_id': 'Skill_ID',
                'name': 'Skill_Name',
                'category': 'Category',
                'subcategory': 'Subcategory',
                'type': 'SkillType',
                'latest_version': 'Latest_Version'
            }
            
            # Select available columns (some may not exist in all datasets)
            available_columns = [col for col in column_mapping.keys() if col in df.columns]
            df_mapped = df[available_columns].rename(columns=column_mapping)
            
            # Add default values for missing columns
            required_columns = ['Skill_ID', 'Skill_Name', 'Category', 'Subcategory', 'SkillType', 'Latest_Version']
            for col in required_columns:
                if col not in df_mapped.columns:
                    df_mapped[col] = ''
            
            # Clean data
            df_mapped = df_mapped.fillna('')
            df_mapped = df_mapped.drop_duplicates(subset=['Skill_ID'])  # Remove duplicates
            
            # Add placeholder metadata columns
            df_mapped['Market_Demand'] = ''
            df_mapped['Rarity_Score'] = None
            
            # Load into database in chunks (large dataset)
            chunk_size = 10000
            with sqlite3.connect(self.db_path) as conn:
                df_mapped.to_sql('skills', conn, if_exists='append', index=False, chunksize=chunk_size)
                
                # Get row count for stats
                cursor = conn.execute("SELECT COUNT(*) FROM skills")
                row_count = cursor.fetchone()[0]
                
            self.load_stats['skills'] = {
                'rows_loaded': len(df_mapped),
                'total_rows': row_count,
                'source_file': str(file_path)
            }
            
            logger.info(f"Loaded {len(df_mapped)} skill records")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load skills library: {e}")
            return False
    
    def _load_job_skill_mapping(self, file_path: Path) -> bool:
        """Load job-skill mapping data into job_skills table."""
        try:
            logger.info(f"Loading job-skill mapping from {file_path}")
            
            # Read CSV
            df = pd.read_csv(file_path)
            
            # Map columns to database schema
            column_mapping = {
                'JobProfileID': 'JobProfileID',
                'Skill_ID': 'Skill_ID'
            }
            
            # Select and rename columns
            available_columns = [col for col in column_mapping.keys() if col in df.columns]
            df_mapped = df[available_columns].rename(columns=column_mapping)
            
            # Add default weight column
            df_mapped['Skill_Weight'] = 1.0  # Default weight
            
            # Clean data
            df_mapped = df_mapped.fillna('')
            df_mapped = df_mapped[df_mapped['JobProfileID'] != '']  # Remove empty JobProfileIDs
            df_mapped = df_mapped[df_mapped['Skill_ID'] != '']       # Remove empty skill IDs
            
            # Load into database
            with sqlite3.connect(self.db_path) as conn:
                df_mapped.to_sql('job_skills', conn, if_exists='append', index=False)
                
                # Get row count for stats
                cursor = conn.execute("SELECT COUNT(*) FROM job_skills")
                row_count = cursor.fetchone()[0]
                
            self.load_stats['job_skills'] = {
                'rows_loaded': len(df_mapped),
                'total_rows': row_count,
                'source_file': str(file_path)
            }
            
            logger.info(f"Loaded {len(df_mapped)} job-skill mappings")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load job-skill mapping: {e}")
            return False
    
    def _load_workforce_context(self, file_path: Path) -> bool:
        """Load workforce context data into positions table with JobProfileID enrichment."""
        try:
            logger.info(f"Loading workforce context from {file_path}")
            
            # Read workforce context CSV
            df_positions = pd.read_csv(file_path, low_memory=False)
            
            # Read position-job mapping CSV for enrichment
            mapping_file = file_path.parent.parent / "job_architecture_to_positions_mapping" / "position_job_mapping.csv"
            if mapping_file.exists():
                logger.info(f"Loading position-job mapping from {mapping_file}")
                df_mapping = pd.read_csv(mapping_file)
                
                # Merge positions with JobProfileID mapping
                df_enriched = df_positions.merge(
                    df_mapping, 
                    left_on='Position Number', 
                    right_on='Position_Number',
                    how='left'  # Keep all positions, even without job mapping
                )
                
                # Log enrichment statistics
                positions_with_jobs = df_enriched['JobProfileID'].notna().sum()
                total_positions = len(df_enriched)
                enrichment_rate = (positions_with_jobs / total_positions * 100) if total_positions > 0 else 0
                logger.info(f"Position enrichment: {positions_with_jobs:,} of {total_positions:,} positions have JobProfileID ({enrichment_rate:.1f}%)")
                
                # Use enriched dataframe
                df = df_enriched
            else:
                logger.warning(f"Position-job mapping file not found: {mapping_file}")
                df = df_positions
                # Add empty JobProfileID column if mapping not available
                df['JobProfileID'] = ''
            
            # Map columns to database schema (flexible mapping)
            column_mapping = {
                'Position Number': 'Position Number',
                'JobProfileID': 'JobProfileID',  # Now included directly
                'Employee Number': 'Employee Number',
                # Organizational hierarchy mapping
                'ORG_UNIT_NAME_2': 'Division',
                'ORG_UNIT_NAME_3': 'Business_Unit', 
                'ORG_UNIT_NAME_4': 'Team',
                'ORG_UNIT_NAME_5': 'SubTeam',
                'ORG_UNIT_NAME_6': 'Function',
                'ORG_UNIT_NAME_7': 'SubFunction',
                'ORG_UNIT_NAME_8': 'Org_Level_8',
                'ORG_UNIT_NAME_9': 'Org_Level_9',
                'ORG_UNIT_NAME_10': 'Org_Level_10',
                # Geographic context
                'Location': 'Location',
                'Rg': 'Rg',
                'Cty': 'Cty',
                # Employment details
                'Employee Group': 'Employee Group',
                'Salary Group': 'Salary Group',
                'Employee Subgroup': 'Employee Subgroup'
            }
            
            # Select available columns and rename
            available_columns = [col for col in column_mapping.keys() if col in df.columns]
            df_mapped = df[available_columns].rename(columns=column_mapping)
            
            # Ensure JobProfileID is preserved if it exists (from merge process)
            if 'JobProfileID' in df.columns and 'JobProfileID' not in df_mapped.columns:
                df_mapped['JobProfileID'] = df['JobProfileID']
            
            # Ensure required columns exist with defaults
            required_columns = ['Position Number', 'JobProfileID', 'Employee Number',
                              'Division', 'Business_Unit', 'Team', 'SubTeam', 'Function', 'SubFunction',
                              'Org_Level_8', 'Org_Level_9', 'Org_Level_10',
                              'Location', 'Rg', 'Cty',
                              'Employee Group', 'Salary Group', 'Employee Subgroup']
            
            for col in required_columns:
                if col not in df_mapped.columns:
                    df_mapped[col] = ''
            
            # Clean data
            df_mapped = df_mapped.fillna('')
            
            # Remove rows with empty Position Number
            df_mapped = df_mapped[df_mapped['Position Number'] != '']
            
            # Load into database
            with sqlite3.connect(self.db_path) as conn:
                df_mapped.to_sql('positions', conn, if_exists='append', index=False)
                
                # Get row count for stats
                cursor = conn.execute("SELECT COUNT(*) FROM positions")
                row_count = cursor.fetchone()[0]
                
            self.load_stats['positions'] = {
                'rows_loaded': len(df_mapped),
                'total_rows': row_count,
                'source_file': str(file_path),
                'enrichment_rate': enrichment_rate if 'enrichment_rate' in locals() else 0
            }
            
            logger.info(f"Loaded {len(df_mapped)} position records")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load workforce context: {e}")
            return False
    
    def load_single_dataset(self, dataset_name: str, file_path: str) -> bool:
        """
        Load a single dataset by name using configuration.
        
        Args:
            dataset_name: Name of dataset ('jobs', 'skills', 'job_skills', 'positions')
            file_path: Path to CSV file
            
        Returns:
            True if loaded successfully
        """
        file_path_obj = Path(file_path)
        
        if not file_path_obj.exists():
            logger.error(f"File not found: {file_path}")
            return False
        
        # Get dataset configuration
        data_sources = self.config.get('data_sources', {})
        if dataset_name not in data_sources:
            logger.error(f"Dataset {dataset_name} not found in configuration")
            return False
        
        dataset_config = data_sources[dataset_name]
        return self._load_dataset_from_config(dataset_name, file_path_obj, dataset_config)
    
    def _print_load_summary(self) -> None:
        """Print summary of all data loading operations."""
        print("\n=== Data Loading Summary ===")
        
        total_rows = 0
        for table_name, stats in self.load_stats.items():
            rows = stats['rows_loaded']
            total_rows += rows
            print(f"✓ {table_name}: {rows:,} rows loaded")
            print(f"  Source: {Path(stats['source_file']).name}")
        
        print(f"\nTotal records loaded: {total_rows:,}")
        print("=" * 31)
    
    def get_load_statistics(self) -> Dict:
        """
        Get detailed loading statistics.
        
        Returns:
            Dictionary with loading statistics
        """
        return self.load_stats.copy()
    
    def verify_foreign_keys(self) -> Dict[str, bool]:
        """
        Verify foreign key relationships are satisfied.
        
        Returns:
            Dictionary with validation results for each relationship
        """
        try:
            results = {}
            
            with sqlite3.connect(self.db_path) as conn:
                # Check job_similarities foreign keys
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM job_similarities js 
                    WHERE js.job_from NOT IN (SELECT JobProfileID FROM jobs)
                """)
                orphaned_from = cursor.fetchone()[0]
                results['job_similarities_from'] = orphaned_from == 0
                
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM job_similarities js 
                    WHERE js.job_to NOT IN (SELECT JobProfileID FROM jobs)
                """)
                orphaned_to = cursor.fetchone()[0]
                results['job_similarities_to'] = orphaned_to == 0
                
                # Check positions foreign keys (direct JobProfileID relationship)
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM positions p 
                    WHERE p.JobProfileID IS NOT NULL AND p.JobProfileID != '' 
                      AND p.JobProfileID NOT IN (SELECT JobProfileID FROM jobs)
                """)
                orphaned_positions = cursor.fetchone()[0]
                results['positions_jobs'] = orphaned_positions == 0
                
                # Check job_skills foreign keys
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM job_skills js 
                    WHERE js.JobProfileID NOT IN (SELECT JobProfileID FROM jobs)
                """)
                orphaned_job_skills = cursor.fetchone()[0]
                results['job_skills_jobs'] = orphaned_job_skills == 0
                
            return results
            
        except Exception as e:
            logger.error(f"Foreign key verification failed: {e}")
            return {} 