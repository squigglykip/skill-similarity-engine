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

from datetime import datetime

from ..config.architectural_config_manager import get_config_manager

from skill_similarity_engine.config.architectural_config_manager import ConfigurationAdapter



logger = logging.getLogger(__name__)





class DataLoader:

    """Loads CSV data into SQLite business context database."""

    

    def __init__(self, db_path: str, config_path: Optional[str] = None):

        """

        Initialize data loader (NO hardcoded paths - configuration-driven).

        

        Args:

            db_path: Path to SQLite database file

            config_path: Optional path to YAML configuration file (uses architectural config if None)

        """

        self.db_path = Path(db_path)

        

        # Use architectural configuration manager (NO hardcoded values)

        self.config_manager = get_config_manager()

        

        # Get config path from architectural configuration if not provided

        if config_path is None:

            config_search_paths = self.config_manager.get_nested_value(

                'business_context', 'database', 'file_discovery', 'config_search_paths',

                default=["config/data/sources.yaml"]  # Fallback to known path

            )

            self.config_path = None

            for search_path in config_search_paths:

                path = Path(search_path)

                if path.exists():

                    self.config_path = path

                    break

            

            if self.config_path is None:

                if config_search_paths:

                    self.config_path = Path(config_search_paths[0])  # Use first as default

                else:

                    raise FileNotFoundError(

                        "No configuration search paths found in architectural configuration. "

                        "Please check config/architectural_config.yaml and config/modules/business_context/database.yaml"

                    )

        else:

            self.config_path = Path(config_path)

        

        self.load_stats = {}

        self.config = self._load_config()

    

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file with variable substitution."""
        try:
            if self.config_path and self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                
                # Use architectural configuration manager for variable substitution
                # This allows resolving variables like ${files.job_skill_mapping}
                full_config = self.config_manager._config  # Access the full config for variable resolution
                adapter = ConfigurationAdapter(full_config)
                
                # Process variable substitution on the entire configuration
                processed_config = adapter._substitute_dict_variables(config)
                
                logger.info(f"Loaded data sources configuration from {self.config_path}")
                return processed_config
            else:
                logger.warning(f"Configuration file not found: {self.config_path}")
                return self._get_default_config()
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return self._get_default_config()
    

    def _get_default_config(self) -> Dict[str, Any]:
        """
        INTENTIONALLY BROKEN: No hardcoded fallback values allowed.
        
        This method now raises an exception to force proper configuration file discovery.
        Following the design principle: "fully object-oriented with no hardcoded values 
        apart from robust /config sections".
        
        If this method is called, it means the configuration system failed to find
        the correct configuration file, which should be investigated and fixed.
        """
        raise FileNotFoundError(
            "Configuration file not found and no hardcoded fallback allowed. "
            f"Expected configuration file at: {self.config_path}. "
            "Please ensure the correct configuration file exists or fix the configuration path discovery. "
            "Design principle: No hardcoded values outside of /config sections."
        )

        

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
        # Use the sequence from configuration, fallback to hardcoded if not found
        loading_sequence = self.config.get('loading_sequence', [
            'core_job_architecture', 
            'core_skills_taxonomy', 
            'job_skills',  # Note: config calls this job_skills, table is core_job_skill_requirements
            'core_workforce_current', 
            'position_history'  # Note: config calls this position_history, table is core_position_timeline
        ])

        

        for dataset_name in loading_sequence:

            if dataset_name not in data_sources:

                logger.warning(f"Dataset {dataset_name} not found in configuration")

                continue

                

            dataset_config = data_sources[dataset_name]

            

            # Load from CSV file(s)
            if 'file_pattern' in dataset_config:
                # Handle multiple files with pattern
                import glob
                pattern = str(data_root_path / dataset_config['file_pattern'])
                matching_files = glob.glob(pattern)
                
                if matching_files:
                    logger.info(f"Loading {dataset_name} from {len(matching_files)} files matching pattern: {dataset_config['file_pattern']}")
                    if not self._load_multiple_files_from_config(dataset_name, matching_files, dataset_config):
                        logger.error(f"Failed to load {dataset_name}")
                        success = False
                    else:
                        logger.info(f"✅ Successfully loaded {dataset_name}")
                else:
                    logger.warning(f"No files found matching pattern: {pattern}")
                    success = False
            else:
                # Handle single file
                file_path = data_root_path / dataset_config['file_path']
                
                if file_path.exists():
                    logger.info(f"Loading {dataset_name} from {file_path}")
                    if not self._load_dataset_from_config(dataset_name, file_path, dataset_config):
                        logger.error(f"Failed to load {dataset_name}")
                        success = False
                    else:
                        logger.info(f"✅ Successfully loaded {dataset_name}")
                else:
                    logger.warning(f"Data file not found: {file_path}")
                    success = False

        

        # Load career pathways from pre-computed parquet file (if available)

        if success:

            try:

                self._load_career_pathways_from_parquet()

            except Exception as e:

                logger.warning(f"Failed to load pre-computed career pathways: {e}")

                logger.info("Career pathways can be generated using the precompute pipeline (main.py option 1)")

                # Don't fail the entire process if career pathways loading fails

        

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

            

            # Handle enrichment if configured (new flexible format)

            if 'enrichment' in dataset_config:

                df = self._apply_enrichment(df, dataset_config['enrichment'], dataset_name, file_path)

            

            # Get column mapping from configuration

            column_mapping = dataset_config.get('column_mapping', {})

            

            # Select and rename columns based on mapping

            available_columns = [col for col in column_mapping.keys() if col in df.columns]

            if not available_columns:

                logger.error(f"No expected columns found in {file_path}")

                return False

                

            df_mapped = df[available_columns].rename(columns=column_mapping)

            

            # Handle primary key generation if configured (after column mapping)

            if 'primary_key_generation' in dataset_config:

                df_mapped = self._apply_primary_key_generation(df_mapped, dataset_config['primary_key_generation'])

            

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

            elif dataset_name == 'positions' and 'Employee Number' in df_mapped.columns:

                # Remove rows with empty Employee Number (primary key)

                df_mapped = df_mapped[df_mapped['Employee Number'] != '']

                # Remove duplicate Employee Numbers if they exist (each employee should appear only once)

                initial_count = len(df_mapped)

                df_mapped = df_mapped.drop_duplicates(subset=['Employee Number'])

                final_count = len(df_mapped)

                if initial_count > final_count:

                    logger.info(f"Removed {initial_count - final_count} duplicate Employee Numbers")

            elif dataset_name == 'job_skills':

                df_mapped = df_mapped[df_mapped['JobProfileID'] != '']

                df_mapped = df_mapped[df_mapped['Skill_ID'] != '']

            elif dataset_name == 'skills' and 'Skill_ID' in df_mapped.columns:

                df_mapped = df_mapped[df_mapped['Skill_ID'] != '']

                df_mapped = df_mapped.drop_duplicates(subset=['Skill_ID'])

            elif dataset_name == 'position_history' and 'position_timeline_id' in df_mapped.columns:

                # Remove duplicates based on the generated primary key to avoid UNIQUE constraint failures

                initial_count = len(df_mapped)

                df_mapped = df_mapped.drop_duplicates(subset=['position_timeline_id'])

                final_count = len(df_mapped)

                if initial_count > final_count:

                    logger.info(f"Removed {initial_count - final_count} duplicate position timeline records")

            

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

        """Load enhanced job architecture data into jobs table with 16-column schema support."""

        try:

            logger.info(f"Loading job architecture from {file_path}")

            

            # Read CSV with proper data types

            df = pd.read_csv(file_path)

            

            # Define flexible column mapping for job architecture data

            # This supports both old schema (6 columns) and new schema (16 columns)

            flexible_mapping = {

                'JobProfileID': 'JobProfileID',

                'JobProfile': 'JobProfile', 

                'JobID': 'JobID',

                'Job': 'Job',

                'ProfileTitleSuffix': 'ProfileTitleSuffix',

                'ManagementLevel': 'ManagementLevel',

                'JobSubFunctionID': 'JobSubFunctionID',

                'JobSubFunction': 'JobSubFunction',

                'JobFunctionID': 'JobFunctionID',

                'JobFunction': 'JobFunction',

                'JobCategoryID': 'JobCategoryID',

                'JobCategory': 'JobCategory',

                'Customer Facing': 'Customer_Facing',

                'is Banker': 'is_Banker',

                'Executive Leadership Group': 'Executive_Leadership_Group',

                'Accountability Scope': 'Accountability_Scope'

            }

            

            # Alternative mappings for legacy compatibility

            if 'JobFamily' in df.columns:

                flexible_mapping['JobFamily'] = 'JobFamily'  # Legacy compatibility

            if 'JobFamilyGroup' in df.columns:

                flexible_mapping['JobFamilyGroup'] = 'JobFamilyGroup'  # Legacy compatibility

            

            # Select available columns (support both old 6-column and new 14-column files)

            available_columns = [col for col in flexible_mapping.keys() if col in df.columns]

            df_mapped = df[available_columns].rename(columns={k: flexible_mapping[k] for k in available_columns})

            

            # Add missing columns with default values for backward compatibility

            required_columns = list(flexible_mapping.values())

            for col in required_columns:

                if col not in df_mapped.columns:

                    df_mapped[col] = ''  # Default empty string for missing columns

            

            # Clean data - handle nulls appropriately

            # For nullable fields, preserve None; for others, use empty strings

            nullable_fields = ['Customer_Facing', 'is_Banker', 'Executive_Leadership_Group', 'Accountability_Scope']

            for col in df_mapped.columns:

                if col in nullable_fields:

                    # Keep nulls as None for nullable fields, but convert NaN to None

                    df_mapped[col] = df_mapped[col].replace({pd.NA: None, '': None})

                else:

                    # Convert nulls to empty strings for non-nullable fields

                    df_mapped[col] = df_mapped[col].fillna('')

            

            logger.info(f"Processing {len(df_mapped)} job records with {len(available_columns)} columns")

            logger.debug(f"Available columns: {available_columns}")

            

            # Load into database

            with sqlite3.connect(self.db_path) as conn:

                df_mapped.to_sql('jobs', conn, if_exists='append', index=False)

                

                # Get row count for stats

                cursor = conn.execute("SELECT COUNT(*) FROM jobs")

                row_count = cursor.fetchone()[0]

                

            self.load_stats['jobs'] = {

                'rows_loaded': len(df_mapped),

                'total_rows': row_count,

                'source_file': str(file_path),

                'columns_loaded': len(available_columns),

                'schema_version': '16-column' if len(available_columns) > 6 else '6-column'

            }

            

            logger.info(f"âœ… Loaded {len(df_mapped)} job records with {self.load_stats['jobs']['schema_version']} schema")

            return True

            

        except Exception as e:

            logger.error(f"Failed to load job architecture: {e}")

            return False

    

    def _load_skills_library(self, file_path: Path) -> bool:

        """Load enhanced comprehensive skills library into skills table with 18-column schema support."""

        try:

            logger.info(f"Loading skills library from {file_path}")

            

            # Read CSV - handle large file efficiently

            df = pd.read_csv(file_path, low_memory=False)

            

            # Enhanced column mapping for 18-column schema

            column_mapping = {

                # Core fields (existing mapping)

                'id': 'Skill_ID',                          # Primary key

                'name': 'Skill_Name',                      # Skill name

                'category_name': 'Category',               # Main category

                'subcategory_name': 'Subcategory',         # Subcategory

                'type': 'SkillType',                       # Skill type

                'source_version': 'Latest_Version',        # Version tracking

                

                # Enhanced 18-column schema fields

                'category_id': 'category_id',              # Lightcast category ID

                'description': 'description',              # Detailed description

                'descriptionSource': 'descriptionSource',  # Source of description

                'infoUrl': 'Info_URL',                     # Lightcast URL (fixed mapping)

                'isLanguage': 'Is_Language',               # Boolean: is language skill (fixed mapping)

                'isSoftware': 'isSoftware',               # Boolean: is software skill

                'subcategory_id': 'subcategory_id',       # Lightcast subcategory ID

                'tag_wikipediaExtract': 'tag_wikipediaExtract',  # Wikipedia extract

                'tag_wikipediaUrl': 'tag_wikipediaUrl',   # Wikipedia URL

                'tags': 'tags',                           # JSON field

                'type_id': 'type_id',                     # Lightcast type ID

                'type_name': 'type_name'                  # Human-readable type name

            }

            

            # Select available columns (support both old and new schema files)

            available_columns = [col for col in column_mapping.keys() if col in df.columns]

            df_mapped = df[available_columns].rename(columns={k: column_mapping[k] for k in available_columns})

            

            # Add default values for missing columns

            all_db_columns = list(column_mapping.values()) + ['Market_Demand', 'Rarity_Score']

            for col in all_db_columns:

                if col not in df_mapped.columns:

                    if col in ['Market_Demand']:

                        df_mapped[col] = ''

                    elif col in ['Rarity_Score', 'category_id', 'subcategory_id']:

                        df_mapped[col] = None

                    elif col in ['isLanguage', 'isSoftware']:

                        df_mapped[col] = False

                    else:

                        df_mapped[col] = ''

            

            # Clean and validate data

            df_mapped = df_mapped.fillna('')  # Fill NaN with empty strings for text fields

            

            # Handle boolean fields properly

            if 'isLanguage' in df_mapped.columns:

                df_mapped['isLanguage'] = df_mapped['isLanguage'].astype(bool)

            if 'isSoftware' in df_mapped.columns:

                df_mapped['isSoftware'] = df_mapped['isSoftware'].astype(bool)

            

            # Handle JSON fields - ensure they're strings

            json_fields = ['tags']

            for field in json_fields:

                if field in df_mapped.columns:

                    df_mapped[field] = df_mapped[field].astype(str)

            

            # Remove duplicates based on Skill_ID

            initial_count = len(df_mapped)

            df_mapped = df_mapped.drop_duplicates(subset=['Skill_ID'])

            duplicates_removed = initial_count - len(df_mapped)

            if duplicates_removed > 0:

                logger.info(f"Removed {duplicates_removed} duplicate skills")

            

            logger.info(f"Processing {len(df_mapped)} skills with {len(available_columns)} columns")

            logger.debug(f"Available columns: {available_columns}")

            

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

                'source_file': str(file_path),

                'columns_loaded': len(available_columns),

                'schema_version': '18-column' if len(available_columns) > 6 else 'legacy',

                'duplicates_removed': duplicates_removed

            }

            

            logger.info(f"âœ… Loaded {len(df_mapped)} skill records with {self.load_stats['skills']['schema_version']} schema")

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

                'Position Name': 'Position Name',

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

            required_columns = ['Position Number', 'Position Name', 'JobProfileID', 'Employee Number',

                              'Division', 'Business_Unit', 'Team', 'SubTeam', 'Function', 'SubFunction',

                              'Org_Level_8', 'Org_Level_9', 'Org_Level_10',

                              'Location', 'Rg', 'Cty',

                              'Employee Group', 'Salary Group', 'Employee Subgroup']

            

            for col in required_columns:

                if col not in df_mapped.columns:

                    df_mapped[col] = ''

            

            # Clean data

            df_mapped = df_mapped.fillna('')

            

            # Remove rows with empty Employee Number (primary key)

            df_mapped = df_mapped[df_mapped['Employee Number'] != '']

            

            # Remove duplicate Employee Numbers if they exist (each employee should appear only once)

            initial_count = len(df_mapped)

            df_mapped = df_mapped.drop_duplicates(subset=['Employee Number'])

            final_count = len(df_mapped)

            if initial_count > final_count:

                logger.info(f"Removed {initial_count - final_count} duplicate Employee Numbers")

            

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
    
    def _load_multiple_files_from_config(self, dataset_name: str, file_paths: List[str], dataset_config: Dict[str, Any]) -> bool:
        """Load and combine multiple CSV files for a single dataset."""
        try:
            # Simply call the existing method for each file, letting it handle the database appending
            total_rows_loaded = 0
            
            for file_path in sorted(file_paths):  # Sort to ensure consistent order
                file_path_obj = Path(file_path)
                logger.debug(f"Loading file: {file_path_obj.name}")
                
                # Use existing single-file loading method
                if self._load_dataset_from_config(dataset_name, file_path_obj, dataset_config):
                    # Get the row count from load_stats if available
                    if dataset_name in self.load_stats:
                        total_rows_loaded += self.load_stats[dataset_name].get('rows_loaded', 0)
                else:
                    logger.warning(f"Failed to load {file_path_obj.name}")
            
            logger.info(f"Loaded total of {total_rows_loaded} rows from {len(file_paths)} files")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load multiple files for {dataset_name}: {e}")
            return False
    
# Note: Dataset generation methods removed - all datasets now loaded from CSV files

    def _print_load_summary(self) -> None:

        """Print summary of all data loading operations."""

        print("\n=== Data Loading Summary ===")

        

        total_rows = 0

        for table_name, stats in self.load_stats.items():

            rows = stats['rows_loaded']

            total_rows += rows

            print(f"✅ {table_name}: {rows:,} rows loaded")

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

                

                if orphaned_positions > 0:

                    logger.warning(f"Found {orphaned_positions} positions with invalid JobProfileID references")

                

                # Log position statistics for monitoring

                cursor = conn.execute("SELECT COUNT(*) FROM positions")

                total_employees = cursor.fetchone()[0]

                

                cursor = conn.execute("SELECT COUNT(DISTINCT \"Position Number\") FROM positions")

                unique_positions = cursor.fetchone()[0]

                

                cursor = conn.execute("""

                    SELECT COUNT(*) FROM positions 

                    WHERE JobProfileID IS NOT NULL AND JobProfileID != ''

                """)

                positions_with_jobs = cursor.fetchone()[0]

                

                logger.info(f"Position statistics: {total_employees:,} employees in {unique_positions:,} unique positions")

                logger.info(f"Job mapping: {positions_with_jobs:,} employees have JobProfileID assignments")

                

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

    

    def _load_career_pathways_from_parquet(self) -> None:

        """Load pre-computed career pathways from parquet file."""

        logger.info("ðŸ“¦ Loading pre-computed career pathways from parquet...")

        

        # Look for career pathways parquet file in the models directory

        from pathlib import Path

        import pandas as pd

        

        # Look for the most recent career pathways file with daily folder strategy

        models_dir = Path("models")

        parquet_files = []

        

        if models_dir.exists():

            # Search in quarterly model directories

            for quarter_dir in models_dir.glob("*"):

                if quarter_dir.is_dir():

                    # Priority 1: Search in daily folders (YYYY-MM-DD format)

                    import re

                    for daily_dir in quarter_dir.iterdir():

                        if daily_dir.is_dir() and re.match(r'^\d{4}-\d{2}-\d{2}$', daily_dir.name):

                            pathways_file = daily_dir / "career_pathways.parquet"

                            if pathways_file.exists():

                                parquet_files.append(pathways_file)

                    

                    # Priority 2: Legacy precompute directories (backward compatibility)

                    for precompute_dir in quarter_dir.glob("precompute_*"):

                        pathways_file = precompute_dir / "career_pathways.parquet"

                        if pathways_file.exists():

                            parquet_files.append(pathways_file)

        

        # Also check data/precomputed directory (legacy support)

        data_dir = Path("data/precomputed")

        if data_dir.exists():

            for precompute_dir in data_dir.glob("precompute_*"):

                pathways_file = precompute_dir / "career_pathways.parquet"

                if pathways_file.exists():

                    parquet_files.append(pathways_file)

        

        if not parquet_files:

            raise FileNotFoundError(

                "No pre-computed career pathways parquet file found. "

                "Please run the precompute pipeline first (main.py option 1 â†’ 2)"

            )

        

        # Use the most recent file

        latest_file = max(parquet_files, key=lambda p: p.stat().st_mtime)

        logger.info(f"ðŸ“ Loading career pathways from: {latest_file}")

        

        try:

            # Load parquet file

            pathways_df = pd.read_parquet(latest_file)

            logger.info(f"ðŸ“Š Loaded {len(pathways_df):,} career pathway relationships from parquet")

            

            # Create database connection

            conn = sqlite3.connect(self.db_path)

            cursor = conn.cursor()

            

            try:

                # Clear existing career pathways data

                cursor.execute("DELETE FROM career_pathways")

                

                # Check if DataFrame is empty

                if len(pathways_df) == 0:

                    logger.warning("ðŸ“Š No career pathway relationships found in parquet file")

                    conn.commit()

                    return

                

                # Convert DataFrame to list of tuples for insertion

                pathway_records = [

                    (

                        row['source_job_id'],

                        row['target_job_id'],

                        row['similarity_rank'],

                        row['similarity_score'],

                        row['skill_overlap_score'],

                        row['shared_skills_count'],

                        row['career_move_type'],

                        row['difficulty_score']

                    )

                    for _, row in pathways_df.iterrows()

                ]

                

                # Bulk insert career pathway records

                insert_query = """

                    INSERT INTO career_pathways (

                        source_job_id, target_job_id, similarity_rank, similarity_score,

                        skill_overlap_score, shared_skills_count, career_move_type, difficulty_score

                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)

                """

                

                cursor.executemany(insert_query, pathway_records)

                conn.commit()

                

                logger.info(f"âœ… Successfully loaded {len(pathway_records):,} career pathway relationships into database")

                

                # Log distribution by move type (only if we have data)

                if len(pathways_df) > 0:

                    move_type_counts = pathways_df['career_move_type'].value_counts().to_dict()

                    logger.info("ðŸ“Š Career move type distribution:")

                    for move_type, count in sorted(move_type_counts.items()):

                        percentage = (count / len(pathways_df)) * 100

                        logger.info(f"   - {move_type}: {count:,} ({percentage:.1f}%)")

                

            finally:

                conn.close()

                

        except Exception as e:

            logger.error(f"Failed to load career pathways from parquet: {e}")

            raise 

    def _apply_enrichment(self, df: pd.DataFrame, enrichment_config: Dict[str, Any], dataset_name: str, file_path: Path) -> pd.DataFrame:
        """
        Apply enrichment to a DataFrame using the new flexible enrichment configuration format.
        
        Args:
            df: Source DataFrame to enrich
            enrichment_config: Enrichment configuration from sources.yaml
            dataset_name: Name of the dataset being processed
            file_path: Path to the source CSV file
            
        Returns:
            Enriched DataFrame with additional columns
        """
        try:
            logger.info(f"Applying enrichment to {dataset_name}...")
            
            # Handle each enrichment column separately
            for enrich_col_name, enrich_config in enrichment_config.items():
                if isinstance(enrich_config, dict) and 'source_file' in enrich_config:
                    # Get enrichment mapping file path
                    mapping_file_path = file_path.parent.parent / enrich_config['source_file']
                    
                    if mapping_file_path.exists():
                        logger.info(f"Loading enrichment mapping from {mapping_file_path}")
                        df_mapping = pd.read_csv(mapping_file_path)
                        
                        # Get mapping configuration
                        mapping_key = enrich_config.get('mapping_key', 'Position Number')
                        target_key = enrich_config.get('target_key', 'Position_Number')
                        value_column = enrich_config.get('value_column', 'JobProfileID')
                        
                        # Perform the merge
                        df = df.merge(
                            df_mapping[[target_key, value_column]], 
                            left_on=mapping_key, 
                            right_on=target_key,
                            how='left'
                        )
                        
                        # Rename the enriched column to match the desired name
                        if value_column in df.columns and value_column != enrich_col_name:
                            df = df.rename(columns={value_column: enrich_col_name})
                        
                        # Remove the duplicate mapping key column if it exists
                        if target_key in df.columns and target_key != mapping_key:
                            df = df.drop(columns=[target_key])
                        
                        # Log enrichment statistics
                        enriched_count = df[enrich_col_name].notna().sum()
                        total_count = len(df)
                        enrichment_rate = (enriched_count / total_count * 100) if total_count > 0 else 0
                        
                        logger.info(f"Enrichment success: {enriched_count:,} of {total_count:,} records have {enrich_col_name} ({enrichment_rate:.1f}%)")
                        
                    else:
                        logger.warning(f"Enrichment mapping file not found: {mapping_file_path}")
                        # Add empty column if mapping not available
                        df[enrich_col_name] = ''
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to apply enrichment to {dataset_name}: {e}")
            # Return original DataFrame if enrichment fails
            return df
    
    def _apply_primary_key_generation(self, df: pd.DataFrame, pk_config: Dict[str, str]) -> pd.DataFrame:
        """
        Apply primary key generation based on configuration.
        
        Args:
            df: DataFrame to add primary keys to
            pk_config: Primary key generation configuration
            
        Returns:
            DataFrame with generated primary key columns
        """
        try:
            for pk_column, generation_rule in pk_config.items():
                if '+' in generation_rule:
                    # Handle concatenation rules like "Position_Number + '_' + Week_Ending"
                    parts = [part.strip().strip("'\"") for part in generation_rule.split('+')]
                    
                    # Build the concatenated value
                    df[pk_column] = ''
                    for i, part in enumerate(parts):
                        if part.startswith("'") and part.endswith("'"):
                            # Literal string
                            literal_value = part[1:-1]  # Remove quotes
                            if i == 0:
                                df[pk_column] = literal_value
                            else:
                                df[pk_column] = df[pk_column] + literal_value
                        else:
                            # Column reference
                            if part in df.columns:
                                if i == 0:
                                    df[pk_column] = df[part].astype(str)
                                else:
                                    df[pk_column] = df[pk_column] + df[part].astype(str)
                    
                    logger.info(f"Generated primary key column '{pk_column}' using rule: {generation_rule}")
                
            return df
            
        except Exception as e:
            logger.error(f"Failed to generate primary keys: {e}")
            return df 

