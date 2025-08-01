"""
Enhanced SQLite Schema Builder for NAB Skills Intelligence Platform

Implements the complete 15-table schema design from docs/ENHANCED_DATABASE_SCHEMA.md with:
- Business-meaningful naming conventions (core_*, analytics_*, sys_*)
- Complete schema structure created in Phase 0 (most tables empty initially)
- 5 core data tables populated from CSV sources
- 1 analytics table populated by modules (analytics_movement_patterns)
- Performance indexes for sub-100ms queries
- Configuration-driven design with no hardcoded values
"""

import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..config.architectural_config_manager import get_config_manager

logger = logging.getLogger(__name__)


class SchemaBuilder:
    """Builds enhanced SQLite schema for NAB Skills Intelligence Platform."""
    
    def __init__(self, db_path: str):
        """
        Initialize enhanced schema builder.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.config_manager = get_config_manager()
        
        # Load schema configuration (no hardcoded values)
        # Load the business_context module config and extract database section
        module_config = self.config_manager.get_nested_value(
            'business_context', 'database',
            default=self._get_fallback_schema_config()
        )
        
        # Extract database config if it's wrapped in a module structure
        if isinstance(module_config, dict) and 'database' in module_config:
            self.schema_config = module_config['database']
        else:
            self.schema_config = module_config
        
        # Get schema version from configuration
        self.schema_version = self.schema_config.get('version', '2.0')
        
        # Load table configurations
        self.table_configs = self._load_table_configurations()
        
        # Load SQL templates and metadata
        self.metadata_config = self.schema_config.get('metadata', {})
        
    def create_schema(self, drop_existing: bool = False) -> bool:
        """
        Create complete 15-table enhanced database schema.
        
        Creates ALL table structures to establish complete architecture:
        - 5 Core Data Tables: Fully populated from CSV sources
        - 1 Analytics Table: analytics_movement_patterns (populated by modules)
        - 2 Ready Analytics Tables: analytics_job_similarities (empty), sys_schema_metadata (minimal)
        - 7 Empty Analytics Tables: Created but empty, ready for Phase 1 & 3 algorithms
        
        Args:
            drop_existing: Whether to drop existing tables first
            
        Returns:
            True if schema created successfully
        """
        try:
            total_tables = self.schema_config['tables']['total_count']
            logger.info(f"Creating enhanced database schema ({total_tables} tables) at: {self.db_path}")
            
            # Ensure parent directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                # Enable foreign key constraints
                conn.execute("PRAGMA foreign_keys = ON;")
                
                if drop_existing:
                    logger.info("Dropping existing tables...")
                    self._drop_existing_tables(conn)
                
                # Create complete 15-table schema structure
                self._create_core_data_tables(conn)
                self._create_analytics_tables_phase_0(conn)
                self._create_analytics_tables_phase_1(conn)
                self._create_analytics_tables_phase_3(conn)
                self._create_system_tables(conn)
                
                # Create strategic performance indexes
                self._create_performance_indexes(conn)
                
                # Add enhanced schema metadata
                self._add_enhanced_schema_metadata(conn)
                
                conn.commit()
                logger.info(f"Enhanced database schema ({total_tables} tables) created successfully")
                return True
                
        except Exception as e:
            logger.error(f"Failed to create enhanced schema: {e}")
            return False
    
    def _drop_existing_tables(self, conn: sqlite3.Connection) -> None:
        """Drop all existing tables in dependency order."""
        # Enhanced schema tables (15 tables) - drop in reverse dependency order
        tables = [
            # Analytics tables (dependent on core tables)
            'analytics_bundle_characteristics', 'analytics_specialized_skills', 
            'analytics_skill_demand_trends', 'analytics_skill_bundles', 'analytics_job_families',
            'analytics_job_defining_skills', 'analytics_skill_rarity', 'analytics_job_similarities',
            'analytics_movement_patterns',
            
            # Core relationship tables
            'core_job_skill_requirements',
            
            # Core data tables
            'core_colleague_positions_history', 'core_position_timeline', 'core_workforce_current', 
            'core_skills_taxonomy', 'core_job_architecture',
            
            # System tables
            'sys_schema_metadata'
        ]
        
        for table in tables:
            try:
                conn.execute(f"DROP TABLE IF EXISTS {table};")
                logger.debug(f"Dropped table: {table}")
            except Exception as e:
                logger.warning(f"Could not drop table {table}: {e}")
    
    def _create_core_data_tables(self, conn: sqlite3.Connection) -> None:
        """Create core data tables - Master reference data."""
        core_count = self.schema_config['tables']['core_data_count']
        logger.info(f"Creating core data tables ({core_count} tables)")
        self._create_core_job_architecture_table(conn)
        self._create_core_skills_taxonomy_table(conn)
        self._create_core_job_skill_requirements_table(conn)
        self._create_core_workforce_current_table(conn)
        self._create_core_position_timeline_table(conn)
        self._create_core_colleague_positions_history_table(conn)
        
    def _create_analytics_tables_phase_0(self, conn: sqlite3.Connection) -> None:
        """Create analytics tables ready for Phase 0 (populated by modules)."""
        phase_0_tables = self.schema_config.get('analytics_tables', {}).get('phase_0', {})
        logger.info(f"Creating Phase 0 analytics tables ({len(phase_0_tables)} tables)")
        self._create_analytics_movement_patterns_table(conn)
        
    def _create_analytics_tables_phase_1(self, conn: sqlite3.Connection) -> None:
        """Create analytics tables ready for Phase 1 (empty initially)."""
        phase_1_tables = self.schema_config.get('analytics_tables', {}).get('phase_1', {})
        logger.info(f"Creating Phase 1 analytics tables ({len(phase_1_tables)} tables)")
        self._create_analytics_job_similarities_table(conn)
        self._create_analytics_skill_rarity_table(conn)
        self._create_analytics_job_defining_skills_table(conn)
        
    def _create_analytics_tables_phase_3(self, conn: sqlite3.Connection) -> None:
        """Create analytics tables ready for Phase 3 (empty initially)."""
        phase_3_tables = self.schema_config.get('analytics_tables', {}).get('phase_3', {})
        logger.info(f"Creating Phase 3 analytics tables ({len(phase_3_tables)} tables)")
        self._create_analytics_job_families_table(conn)
        self._create_analytics_skill_bundles_table(conn)
        self._create_analytics_skill_demand_trends_table(conn)
        self._create_analytics_specialized_skills_table(conn)
        self._create_analytics_bundle_characteristics_table(conn)
        
    def _create_system_tables(self, conn: sqlite3.Connection) -> None:
        """Create system metadata tables (1 table)."""
        logger.info("Creating system tables (1 table)")
        self._create_sys_schema_metadata_table(conn)

    # Core Data Tables (5 tables)
    
    def _create_core_job_architecture_table(self, conn: sqlite3.Connection) -> None:
        """Create core_job_architecture table - Complete job framework with all CSV data preserved."""
        sql = """
        CREATE TABLE core_job_architecture (
            -- Core required columns
            JobProfileID TEXT PRIMARY KEY,           -- From CSV: JobProfileID
            JobProfile TEXT NOT NULL,                -- From CSV: JobProfile
            JobFunction TEXT,                        -- From CSV: JobFunction
            JobCategory TEXT,                        -- From CSV: JobCategory
            ManagementLevel TEXT,                    -- From CSV: ManagementLevel
            
            -- ALL additional CSV data (preserve everything)
            JobID TEXT,                              -- From CSV: JobID
            Job TEXT,                                -- From CSV: Job
            ProfileTitleSuffix TEXT,                 -- From CSV: ProfileTitleSuffix
            JobSubFunctionID TEXT,                   -- From CSV: JobSubFunctionID
            JobSubFunction TEXT,                     -- From CSV: JobSubFunction
            JobFunctionID TEXT,                      -- From CSV: JobFunctionID
            JobCategoryID TEXT,                      -- From CSV: JobCategoryID
            Customer_Facing TEXT,                    -- From CSV: Customer Facing
            is_Banker TEXT,                          -- From CSV: is Banker
            Executive_Leadership_Group TEXT,         -- From CSV: Executive Leadership Group
            Accountability_Scope TEXT,              -- From CSV: Accountability Scope
            
            created_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """
        conn.execute(sql)
        logger.debug("Created core_job_architecture table with complete CSV data preservation")
    
    def _create_core_skills_taxonomy_table(self, conn: sqlite3.Connection) -> None:
        """Create core_skills_taxonomy table - Complete skills data with all CSV columns preserved."""
        sql = """
        CREATE TABLE core_skills_taxonomy (
            -- Core required columns
            Skill_ID TEXT PRIMARY KEY,               -- From CSV: id
            Skill_Name TEXT NOT NULL,                -- From CSV: name
            Category TEXT,                          -- From CSV: category_name
            Subcategory TEXT,                       -- From CSV: subcategory_name
            SkillType TEXT,                         -- From CSV: type_name
            
            -- ALL additional CSV data (preserve everything)
            category_id REAL,                       -- From CSV: category_id
            description TEXT,                       -- From CSV: description
            descriptionSource TEXT,                 -- From CSV: descriptionSource
            infoUrl TEXT,                          -- From CSV: infoUrl
            isLanguage BOOLEAN,                     -- From CSV: isLanguage
            isSoftware BOOLEAN,                     -- From CSV: isSoftware
            source_version REAL,                    -- From CSV: source_version
            subcategory_id REAL,                    -- From CSV: subcategory_id
            tag_wikipediaExtract TEXT,              -- From CSV: tag_wikipediaExtract
            tag_wikipediaUrl TEXT,                  -- From CSV: tag_wikipediaUrl
            tags TEXT,                              -- From CSV: tags
            type TEXT,                              -- From CSV: type
            type_id TEXT,                           -- From CSV: type_id
            
            created_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """
        conn.execute(sql)
        logger.debug("Created core_skills_taxonomy table with complete CSV data preservation")
    
    def _create_core_job_skill_requirements_table(self, conn: sqlite3.Connection) -> None:
        """Create core_job_skill_requirements table - Simple job-skill mapping from CSV."""
        sql = """
        CREATE TABLE core_job_skill_requirements (
            -- Core relationship (this is all we have from CSV, and it's perfect)
            JobProfileID TEXT,                      -- From CSV: JobProfileID
            Skill_ID TEXT,                         -- From CSV: Skill_ID
            
            created_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (JobProfileID, Skill_ID),
            FOREIGN KEY (JobProfileID) REFERENCES core_job_architecture(JobProfileID),
            FOREIGN KEY (Skill_ID) REFERENCES core_skills_taxonomy(Skill_ID)
        );
        """
        conn.execute(sql)
        logger.debug("Created core_job_skill_requirements table")
    
    def _create_core_workforce_current_table(self, conn: sqlite3.Connection) -> None:
        """Create core_workforce_current table - Workforce data with 19 available CSV columns preserved."""
        sql = """
        CREATE TABLE core_workforce_current (
            -- Core required columns
            employee_number TEXT PRIMARY KEY,       -- From CSV: Employee Number
            position_number TEXT NOT NULL,          -- From CSV: Position Number
            position_name TEXT,                     -- From CSV: Position Name
            JobProfileID TEXT,                      -- From ENRICHMENT: job_arch_to_positions_mapping
            
            -- Employee classification data
            Employee_Group TEXT,                    -- From CSV: Employee Group
            Employee_Subgroup TEXT,                 -- From CSV: Employee Subgroup
            Salary_Group TEXT,                      -- From CSV: Salary Group
            
            -- Location data
            Location TEXT,                          -- From CSV: Location
            Rg TEXT,                                -- From CSV: Rg
            Cty TEXT,                               -- From CSV: Cty
            
            -- SAP organizational hierarchy (names only - no numbers available in CSV)
            ORG_UNIT_NAME_1 TEXT,                   -- From CSV: ORG_UNIT_NAME_1
            ORG_UNIT_NAME_2 TEXT,                   -- From CSV: ORG_UNIT_NAME_2
            ORG_UNIT_NAME_3 TEXT,                   -- From CSV: ORG_UNIT_NAME_3
            ORG_UNIT_NAME_4 TEXT,                   -- From CSV: ORG_UNIT_NAME_4
            ORG_UNIT_NAME_5 TEXT,                   -- From CSV: ORG_UNIT_NAME_5
            ORG_UNIT_NAME_6 TEXT,                   -- From CSV: ORG_UNIT_NAME_6
            ORG_UNIT_NAME_7 TEXT,                   -- From CSV: ORG_UNIT_NAME_7
            ORG_UNIT_NAME_8 TEXT,                   -- From CSV: ORG_UNIT_NAME_8
            ORG_UNIT_NAME_9 TEXT,                   -- From CSV: ORG_UNIT_NAME_9
            ORG_UNIT_NAME_10 TEXT,                  -- From CSV: ORG_UNIT_NAME_10
            
            created_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (JobProfileID) REFERENCES core_job_architecture(JobProfileID)
        );
        """
        conn.execute(sql)
        logger.debug("Created core_workforce_current table with 19 available CSV columns preserved")
    
    def _create_core_position_timeline_table(self, conn: sqlite3.Connection) -> None:
        """Create core_position_timeline table - Complete position history with all CSV data preserved."""
        sql = """
        CREATE TABLE core_position_timeline (
            position_timeline_id TEXT PRIMARY KEY,  -- Generated: position_number + week_ending
            
            -- Core temporal data
            Week_Ending TEXT,                       -- From CSV: Week Ending
            Position_Number INTEGER,                -- From CSV: Position Number
            JobProfileID TEXT,                      -- From ENRICHMENT: job_arch_to_positions_mapping
            
            -- ALL position history data (preserve everything)
            PosIDLookupKey REAL,                    -- From CSV: PosIDLookupKey
            Organisational_Unit TEXT,               -- From CSV: Organisational Unit
            Cost_Centre_Number INTEGER,             -- From CSV: Cost Centre Number
            Position_Title TEXT,                    -- From CSV: Position Title (100% NULL but preserved)
            People_Leader REAL,                     -- From CSV: People Leader
            Operational BOOLEAN,                    -- From CSV: Operational
            OrgUnitIDLookupKey INTEGER,             -- From CSV: OrgUnitIDLookupKey
            
            created_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (JobProfileID) REFERENCES core_job_architecture(JobProfileID)
        );
        """
        conn.execute(sql)
        logger.debug("Created core_position_timeline table with complete CSV data preservation")
    
    def _create_core_colleague_positions_history_table(self, conn: sqlite3.Connection) -> None:
        """Create core_colleague_positions_history table - Monthly colleague position snapshots for Phase 2 movement analysis."""
        # Create the table
        table_sql = """
        CREATE TABLE core_colleague_positions_history (
            -- Raw CSV data (preserve exact field names)
            "Week Ending" TEXT,                        -- From CSV: Week Ending (DD/MM/YYYY)
            "Employee Number" INTEGER,                  -- From CSV: Employee Number
            "Operational" BOOLEAN,                      -- From CSV: Operational (True/False)
            "Position Start Date" TEXT,                 -- From CSV: Position Start Date (nullable, DD/MM/YYYY)
            "PosIDLookupKey" REAL,                     -- From CSV: PosIDLookupKey (scientific notation) - NOT unique across time
            "Position Number" INTEGER,                  -- From CSV: Position Number
            
            created_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            
            -- Composite primary key: same position can exist across multiple weeks
            PRIMARY KEY ("PosIDLookupKey", "Week Ending")
            
            -- Foreign key relationship to positions (via PosIDLookupKey)
            -- Note: No direct FK constraint due to temporal data complexity
            -- Relationship established through PosIDLookupKey matching
        );
        """
        conn.execute(table_sql)
        
        # Create indexes for Phase 2 movement analysis queries
        indexes = [
            'CREATE INDEX idx_colleague_positions_employee ON core_colleague_positions_history ("Employee Number");',
            'CREATE INDEX idx_colleague_positions_position ON core_colleague_positions_history ("Position Number");',
            'CREATE INDEX idx_colleague_positions_week ON core_colleague_positions_history ("Week Ending");',
            'CREATE INDEX idx_colleague_positions_lookup_key ON core_colleague_positions_history ("PosIDLookupKey");',
            'CREATE INDEX idx_colleague_positions_temporal ON core_colleague_positions_history ("Employee Number", "Week Ending");',
            'CREATE INDEX idx_colleague_positions_movement ON core_colleague_positions_history ("Employee Number", "Position Number", "Week Ending");'
        ]
        
        for index_sql in indexes:
            conn.execute(index_sql)
        
        logger.debug("Created core_colleague_positions_history table with indexes for Phase 2 movement analysis")
    
    # Analytics Tables - Phase 0 (1 table)
    
    def _create_analytics_movement_patterns_table(self, conn: sqlite3.Connection) -> None:
        """Create analytics_movement_patterns table - Aggregated movement patterns (generated by MovementTracker → FactTableBuilder)."""
        sql = """
        CREATE TABLE analytics_movement_patterns (
            movement_pattern_id TEXT PRIMARY KEY,   -- Unique pattern identifier
            movement_month TEXT,                    -- "2024-01", "2024-02", etc.
            from_position TEXT,                     -- Source position
            to_position TEXT,                       -- Target position
            from_job_profile_id TEXT,              -- Source job profile
            to_job_profile_id TEXT,                -- Target job profile
            
            -- Movement metrics
            movement_count INTEGER,                 -- Number of movements
            unique_employees INTEGER,               -- Unique people who made this transition
            avg_days_between REAL,                 -- Average days between positions
            pct_total_movements REAL,              -- Percentage of all movements this month
            
            -- Movement characteristics
            movement_type TEXT,                     -- "Internal", "Promotion", "Lateral", "External"
            skill_similarity_score REAL,           -- Job similarity score
            difficulty_score REAL,                 -- Transition difficulty
            success_rate REAL,                     -- Historical success rate
            
            created_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (from_job_profile_id) REFERENCES core_job_architecture(JobProfileID),
            FOREIGN KEY (to_job_profile_id) REFERENCES core_job_architecture(JobProfileID)
        );
        """
        conn.execute(sql)
        logger.debug("Created analytics_movement_patterns table")
    
    # Analytics Tables - Phase 1 (2 tables)
    
    def _create_analytics_job_similarities_table(self, conn: sqlite3.Connection) -> None:
        """Create analytics_job_similarities table - Enhanced job similarities (populated by Phase 1)."""
        sql = """
        CREATE TABLE analytics_job_similarities (
            similarity_id TEXT PRIMARY KEY,         -- Unique similarity record
            job_from TEXT,                          -- Source JobProfileID
            job_to TEXT,                           -- Target JobProfileID
            
            -- Similarity metrics
            similarity_score REAL,                 -- Basic Jaccard similarity (0-1)
            enhanced_similarity_score REAL,        -- Rarity-weighted + defining skills boost
            rarity_weighted_score REAL,           -- Before defining skills boost
            shared_defining_skills_count INTEGER,  -- Count of shared defining skills
            defining_skill_boost REAL,            -- Actual boost applied (multiplier impact)
            
            -- Skill overlap details
            shared_skills_count INTEGER,           -- Total shared skills
            total_skills_from INTEGER,             -- Total skills in source job
            total_skills_to INTEGER,               -- Total skills in target job
            skill_overlap_percentage REAL,         -- (shared/total_from) * 100
            
            -- Enhanced analytics
            shared_skills TEXT,                    -- JSON array of shared skill IDs
            shared_defining_skills TEXT,           -- JSON array of shared defining skill IDs
            skill_gap_analysis TEXT,              -- JSON object with gap details
            
            calculation_algorithm TEXT,            -- "enhanced_v2", "basic_jaccard"
            created_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (job_from) REFERENCES core_job_architecture(JobProfileID),
            FOREIGN KEY (job_to) REFERENCES core_job_architecture(JobProfileID)
        );
        """
        conn.execute(sql)
        logger.debug("Created analytics_job_similarities table")
    
    def _create_analytics_skill_rarity_table(self, conn: sqlite3.Connection) -> None:
        """Create analytics_skill_rarity table - Complete skill rarity analysis (replaces skill_universe CSV)."""
        sql = """
        CREATE TABLE analytics_skill_rarity (
            skill_id TEXT PRIMARY KEY,              -- References core_skills_taxonomy.Skill_ID
            skill_name TEXT NOT NULL,               -- Human-readable skill name
            category TEXT,                          -- Skill category
            subcategory TEXT,                       -- Skill subcategory
            skill_type TEXT,                        -- Skill type
            
            -- Rarity metrics
            total_profiles_with_skill INTEGER,      -- Number of job profiles requiring this skill
            total_jobs INTEGER,                     -- Total job profiles analyzed
            prevalence_percentage REAL,             -- (profiles_with_skill/total_jobs) * 100
            rarity_category TEXT,                   -- 'rare', 'uncommon', 'common', 'universal'
            rarity_score REAL,                     -- Calculated rarity score (0-1)
            
            -- Defining skills analysis
            is_defining_skill BOOLEAN,              -- True if skill is in top 20% rarest for any job
            defining_for_jobs_count INTEGER,        -- Number of jobs where this is a defining skill
            defining_for_jobs TEXT,                -- JSON array of JobProfileIDs
            
            -- Analysis metadata
            analysis_date TEXT,                     -- When analysis was performed
            algorithm_version TEXT,                 -- Version of rarity calculation algorithm
            created_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (skill_id) REFERENCES core_skills_taxonomy(Skill_ID)
        );
        """
        conn.execute(sql)
        logger.debug("Created analytics_skill_rarity table")
    
    def _create_analytics_job_defining_skills_table(self, conn: sqlite3.Connection) -> None:
        """Create analytics_job_defining_skills table - Job-specific defining skills relationships."""
        sql = """
        CREATE TABLE analytics_job_defining_skills (
            job_profile_id TEXT,                    -- References core_job_architecture.JobProfileID
            skill_id TEXT,                         -- References core_skills_taxonomy.Skill_ID
            skill_name TEXT,                       -- Human-readable skill name
            job_profile TEXT,                      -- Job profile name
            
            -- Skill context
            category TEXT,                         -- Skill category
            subcategory TEXT,                      -- Skill subcategory
            skill_type TEXT,                       -- Skill type
            
            -- Defining skill metrics
            prevalence_percentage REAL,            -- Skill prevalence across all jobs
            total_profiles_with_skill INTEGER,     -- Total profiles with this skill
            rarity_category TEXT,                  -- Rarity classification
            defining_skill_rank INTEGER,           -- Rank among defining skills for this job (1-N)
            defining_skill_score REAL,            -- Defining skill strength score
            
            -- Analysis metadata
            analysis_date TEXT,                    -- When analysis was performed
            percentile_threshold REAL,             -- Percentile used for defining skills (e.g., 20.0)
            created_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            
            PRIMARY KEY (job_profile_id, skill_id),
            FOREIGN KEY (job_profile_id) REFERENCES core_job_architecture(JobProfileID),
            FOREIGN KEY (skill_id) REFERENCES core_skills_taxonomy(Skill_ID)
        );
        """
        conn.execute(sql)
        logger.debug("Created analytics_job_defining_skills table")
    
    # Analytics Tables - Phase 3 (5 tables)
    
    def _create_analytics_job_families_table(self, conn: sqlite3.Connection) -> None:
        """Create analytics_job_families table - Job cluster assignments with business context."""
        sql = """
        CREATE TABLE analytics_job_families (
            job_profile_id TEXT,                    -- References core_job_architecture.JobProfileID
            job_profile TEXT,                       -- Job profile name
            job_function TEXT,                      -- Job function
            job_sub_function TEXT,                  -- Job sub-function
            job_category TEXT,                      -- Job category
            management_level TEXT,                  -- Management level
            
            -- Clustering results
            cluster_id INTEGER,                     -- Cluster identifier
            cluster_name TEXT,                      -- Business-readable cluster name
            cluster_description TEXT,               -- Human-interpretable description
            cluster_rationale TEXT,                -- Explanation of clustering logic
            cluster_size INTEGER,                   -- Number of jobs in cluster
            
            -- Cluster context
            sample_jobs TEXT,                       -- JSON array of representative job examples
            sample_skills TEXT,                     -- JSON array of representative skills
            cluster_confidence REAL,               -- Confidence in cluster assignment (0-1)
            
            -- Quality metrics
            silhouette_score REAL,                 -- Individual job's silhouette score
            intra_cluster_similarity REAL,         -- Average similarity to cluster members
            inter_cluster_distance REAL,           -- Distance to nearest other cluster
            
            -- Analysis metadata
            clustering_algorithm TEXT,             -- "dbscan", "hierarchical", etc.
            algorithm_parameters TEXT,             -- JSON object with algorithm parameters
            analysis_date TEXT,                    -- When clustering was performed
            created_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            
            PRIMARY KEY (job_profile_id, cluster_id),
            FOREIGN KEY (job_profile_id) REFERENCES core_job_architecture(JobProfileID)
        );
        """
        conn.execute(sql)
        logger.debug("Created analytics_job_families table")
    
    def _create_analytics_skill_bundles_table(self, conn: sqlite3.Connection) -> None:
        """Create analytics_skill_bundles table - Skills clustering with business-readable bundle names."""
        sql = """
        CREATE TABLE analytics_skill_bundles (
            skill_id TEXT,                         -- References core_skills_taxonomy.Skill_ID
            skill_name TEXT,                       -- Human-readable skill name
            category TEXT,                         -- Skill category
            subcategory TEXT,                      -- Skill subcategory
            skill_type TEXT,                       -- Skill type
            
            -- Skill usage context
            total_occurrences INTEGER,             -- Total occurrences across all jobs
            jobs_count INTEGER,                    -- Number of jobs requiring this skill
            prevalence_percent REAL,               -- Prevalence across job profiles
            
            -- Clustering results
            cluster_id INTEGER,                    -- Bundle identifier
            bundle_name TEXT,                      -- Business-readable bundle name
            bundle_description TEXT,               -- Human-interpretable description
            bundle_rationale TEXT,                -- Explanation of bundling logic
            bundle_size INTEGER,                   -- Number of skills in bundle
            is_specialized BOOLEAN,                -- Individual vs bundled classification
            
            -- Bundle context
            sample_skills TEXT,                    -- JSON array of representative skills in bundle
            sample_job_functions TEXT,             -- JSON array of job functions using this bundle
            bundle_confidence REAL,               -- Confidence in bundle assignment (0-1)
            
            -- Quality metrics
            silhouette_score REAL,                -- Individual skill's silhouette score
            intra_bundle_similarity REAL,         -- Average similarity to bundle members
            inter_bundle_distance REAL,           -- Distance to nearest other bundle
            
            -- Analysis metadata
            clustering_algorithm TEXT,            -- "dbscan", "hierarchical", etc.
            similarity_method TEXT,               -- "cosine", "jaccard", etc.
            algorithm_parameters TEXT,            -- JSON object with algorithm parameters
            analysis_date TEXT,                   -- When clustering was performed
            created_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            
            PRIMARY KEY (skill_id, cluster_id),
            FOREIGN KEY (skill_id) REFERENCES core_skills_taxonomy(Skill_ID)
        );
        """
        conn.execute(sql)
        logger.debug("Created analytics_skill_bundles table")

    def _create_analytics_skill_demand_trends_table(self, conn: sqlite3.Connection) -> None:
        """Create analytics_skill_demand_trends table - Multi-timeframe skill velocity analysis."""
        sql = """
        CREATE TABLE analytics_skill_demand_trends (
            skill_id TEXT PRIMARY KEY,             -- References core_skills_taxonomy.Skill_ID
            skill_name TEXT,                       -- Human-readable skill name
            category TEXT,                         -- Skill category
            skill_type TEXT,                       -- Skill type
            
            -- Current demand metrics
            jobs_requiring_skill INTEGER,          -- Current jobs requiring this skill
            total_skill_instances INTEGER,         -- Total instances across all profiles
            current_prevalence_percent REAL,       -- Current prevalence percentage
            
            -- Velocity metrics (CAGR - Compound Annual Growth Rate)
            short_term_cagr REAL,                 -- 1 year CAGR
            medium_term_cagr REAL,                -- 2 year CAGR
            long_term_cagr REAL,                  -- 3 year CAGR
            
            -- Trend classification
            velocity_category TEXT,                -- 'accelerating', 'growing', 'stable', 'declining', 'steep_decline'
            trend_direction TEXT,                  -- 'up', 'stable', 'down'
            trend_strength TEXT,                   -- 'strong', 'moderate', 'weak'
            trend_confidence REAL,                -- Confidence in trend analysis (0-1)
            
            -- Movement-based metrics
            total_movements INTEGER,               -- Total movements involving this skill
            total_recency_weighted_movements REAL, -- Recency-weighted movements
            recency_weighted_growth_pct REAL,     -- Growth percentage with recency weighting
            
            -- Forecasting
            projected_demand_1yr REAL,            -- Projected demand in 1 year
            projected_demand_2yr REAL,            -- Projected demand in 2 years
            projected_demand_3yr REAL,            -- Projected demand in 3 years
            
            -- Analysis metadata
            analysis_windows TEXT,                 -- JSON object with analysis timeframes
            velocity_thresholds TEXT,              -- JSON object with categorization thresholds
            data_quality_score REAL,              -- Quality of underlying data (0-1)
            analysis_date TEXT,                    -- When analysis was performed
            created_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (skill_id) REFERENCES core_skills_taxonomy(Skill_ID)
        );
        """
        conn.execute(sql)
        logger.debug("Created analytics_skill_demand_trends table")

    def _create_analytics_specialized_skills_table(self, conn: sqlite3.Connection) -> None:
        """Create analytics_specialized_skills table - Individual specialized/emerging skills not suitable for bundling."""
        sql = """
        CREATE TABLE analytics_specialized_skills (
            skill_id TEXT PRIMARY KEY,             -- References core_skills_taxonomy.Skill_ID
            skill_name TEXT,                       -- Human-readable skill name
            category TEXT,                         -- Skill category
            subcategory TEXT,                      -- Skill subcategory
            skill_type TEXT,                       -- Skill type
            
            -- Specialization metrics
            jobs_count INTEGER,                    -- Number of jobs requiring this skill
            prevalence_percent REAL,              -- Prevalence across job profiles
            specialization_score REAL,            -- How specialized this skill is (0-1)
            rarity_rank INTEGER,                  -- Rank among all skills by rarity
            
            -- Specialization analysis
            specialization_reason TEXT,           -- Why this skill wasn't bundled
            specialization_category TEXT,         -- "emerging", "niche", "expert_level", "legacy"
            market_context TEXT,                  -- Business context for specialization
            
            -- Strategic value
            strategic_importance TEXT,            -- "critical", "important", "niche", "declining"
            skill_lifecycle_stage TEXT,          -- "emerging", "growing", "mature", "declining"
            investment_recommendation TEXT,       -- "invest", "maintain", "monitor", "phase_out"
            
            -- Related context
            related_skills TEXT,                 -- JSON array of related skill IDs
            typical_job_functions TEXT,          -- JSON array of job functions requiring this skill
            training_availability TEXT,          -- Training program availability
            external_market_demand TEXT,         -- External market demand level
            
            -- Analysis metadata
            analysis_methodology TEXT,           -- How specialization was determined
            confidence_level TEXT,               -- "high", "medium", "low"
            last_review_date TEXT,               -- When this was last reviewed
            next_review_date TEXT,               -- When this should be reviewed next
            created_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            
            FOREIGN KEY (skill_id) REFERENCES core_skills_taxonomy(Skill_ID)
        );
        """
        conn.execute(sql)
        logger.debug("Created analytics_specialized_skills table")
    
    def _create_analytics_bundle_characteristics_table(self, conn: sqlite3.Connection) -> None:
        """Create analytics_bundle_characteristics table - Detailed skill bundle characteristics with quality metrics."""
        sql = """
        CREATE TABLE analytics_bundle_characteristics (
            cluster_id INTEGER PRIMARY KEY,        -- Unique bundle identifier
            bundle_name TEXT,                      -- Business-readable bundle name
            bundle_description TEXT,               -- Human-interpretable description
            bundle_rationale TEXT,                -- Explanation of bundling logic
            bundle_size INTEGER,                   -- Number of skills in bundle
            
            -- Bundle composition
            sample_skills TEXT,                    -- JSON array of representative skills
            sample_job_functions TEXT,             -- JSON array of job functions using bundle
            core_skills TEXT,                      -- JSON array of core skills in bundle
            peripheral_skills TEXT,               -- JSON array of peripheral skills
            
            -- Quality metrics
            dominant_category TEXT,                -- Most common skill category in bundle
            category_purity REAL,                 -- Percentage of skills in dominant category
            application_level TEXT,               -- "advanced", "intermediate", "basic"
            specialization_area TEXT,             -- Domain focus area
            average_jobs_per_skill REAL,          -- Average job usage per skill
            
            -- Validation metrics
            taxonomy_alignment_score REAL,        -- Alignment with existing skill taxonomy (0-1)
            silhouette_score REAL,               -- Overall bundle quality metric
            intra_bundle_cohesion REAL,          -- How similar skills are within bundle
            inter_bundle_separation REAL,         -- How distinct this bundle is from others
            
            -- Business context
            business_value_score REAL,           -- Strategic business value (0-1)
            training_feasibility TEXT,           -- "high", "medium", "low"
            skill_complementarity REAL,          -- How well skills complement each other
            market_demand_level TEXT,            -- "high", "medium", "low"
            
            -- Usage patterns
            common_job_families TEXT,            -- JSON array of job families using this bundle
            typical_career_stage TEXT,           -- "entry", "mid", "senior", "expert"
            skill_acquisition_difficulty TEXT,    -- "easy", "moderate", "difficult"
            
            -- Analysis metadata
            clustering_algorithm TEXT,           -- Algorithm used for bundling
            algorithm_parameters TEXT,           -- JSON object with parameters
            quality_validation_date TEXT,        -- When quality was last validated
            business_review_date TEXT,           -- When business context was last reviewed
            created_timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """
        conn.execute(sql)
        logger.debug("Created analytics_bundle_characteristics table")
    
    # System Tables (1 table)
    
    def _create_sys_schema_metadata_table(self, conn: sqlite3.Connection) -> None:
        """Create sys_schema_metadata table - System metadata and versioning."""
        sql = """
        CREATE TABLE sys_schema_metadata (
            metadata_key TEXT PRIMARY KEY,          -- Unique metadata key
            metadata_value TEXT,                    -- Value or JSON object
            metadata_category TEXT,                 -- "schema", "version", "config", "stats"
            description TEXT,                       -- Human-readable description
            
            created_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """
        conn.execute(sql)
        logger.debug("Created sys_schema_metadata table")
    
    def _create_performance_indexes(self, conn: sqlite3.Connection) -> None:
        """Create strategic performance indexes for sub-100ms queries."""
        indexes = [
            # Core job architecture indexes
            "CREATE INDEX idx_core_job_architecture_function ON core_job_architecture(JobFunction);",
            "CREATE INDEX idx_core_job_architecture_category ON core_job_architecture(JobCategory);",
            "CREATE INDEX idx_core_job_architecture_level ON core_job_architecture(ManagementLevel);",
            
            # Core skills taxonomy indexes
            "CREATE INDEX idx_core_skills_taxonomy_category ON core_skills_taxonomy(Category);",
            "CREATE INDEX idx_core_skills_taxonomy_type ON core_skills_taxonomy(SkillType);",
            "CREATE INDEX idx_core_skills_taxonomy_software ON core_skills_taxonomy(isSoftware);",
            
            # Core job skill requirements indexes (critical for similarity calculations)
            "CREATE INDEX idx_core_job_skill_requirements_job ON core_job_skill_requirements(JobProfileID);",
            "CREATE INDEX idx_core_job_skill_requirements_skill ON core_job_skill_requirements(Skill_ID);",
            "CREATE INDEX idx_core_job_skill_requirements_composite ON core_job_skill_requirements(JobProfileID, Skill_ID);",
            
            # Core workforce current indexes (for workforce analytics)
            "CREATE INDEX idx_core_workforce_current_job ON core_workforce_current(JobProfileID);",
            "CREATE INDEX idx_core_workforce_current_org_2 ON core_workforce_current(ORG_UNIT_NAME_2);",
            "CREATE INDEX idx_core_workforce_current_location ON core_workforce_current(Location);",
            "CREATE INDEX idx_core_workforce_current_position ON core_workforce_current(position_number);",
            
            # Core position timeline indexes (for temporal analysis)
            "CREATE INDEX idx_core_position_timeline_week ON core_position_timeline(Week_Ending);",
            "CREATE INDEX idx_core_position_timeline_position ON core_position_timeline(Position_Number);",
            "CREATE INDEX idx_core_position_timeline_job ON core_position_timeline(JobProfileID);",
            "CREATE INDEX idx_core_position_timeline_operational ON core_position_timeline(Operational);",
            
            # Analytics movement patterns indexes (for ML feature engineering)
            "CREATE INDEX idx_analytics_movement_patterns_month ON analytics_movement_patterns(movement_month);",
            "CREATE INDEX idx_analytics_movement_patterns_from ON analytics_movement_patterns(from_job_profile_id);",
            "CREATE INDEX idx_analytics_movement_patterns_to ON analytics_movement_patterns(to_job_profile_id);",
            "CREATE INDEX idx_analytics_movement_patterns_type ON analytics_movement_patterns(movement_type);",
            
            # Analytics job similarities indexes (critical for webapp queries)
            "CREATE INDEX idx_analytics_job_similarities_from ON analytics_job_similarities(job_from, enhanced_similarity_score DESC);",
            "CREATE INDEX idx_analytics_job_similarities_to ON analytics_job_similarities(job_to, enhanced_similarity_score DESC);",
            "CREATE INDEX idx_analytics_job_similarities_score ON analytics_job_similarities(enhanced_similarity_score DESC);",
            "CREATE INDEX idx_analytics_job_similarities_algorithm ON analytics_job_similarities(calculation_algorithm);",
            
            # Analytics skill rarity indexes (for defining skills lookup)
            "CREATE INDEX idx_analytics_skill_rarity_category ON analytics_skill_rarity(rarity_category);",
            "CREATE INDEX idx_analytics_skill_rarity_prevalence ON analytics_skill_rarity(prevalence_percentage);",
            "CREATE INDEX idx_analytics_skill_rarity_defining ON analytics_skill_rarity(is_defining_skill);",
            
            # Analytics job defining skills indexes (for similarity calculations)
            "CREATE INDEX idx_analytics_job_defining_skills_job ON analytics_job_defining_skills(job_profile_id);",
            "CREATE INDEX idx_analytics_job_defining_skills_skill ON analytics_job_defining_skills(skill_id);",
            "CREATE INDEX idx_analytics_job_defining_skills_rank ON analytics_job_defining_skills(defining_skill_rank);",
            
            # Phase 3 analytics indexes (for business intelligence)
            "CREATE INDEX idx_analytics_job_families_cluster ON analytics_job_families(cluster_id);",
            "CREATE INDEX idx_analytics_job_families_function ON analytics_job_families(job_function);",
            "CREATE INDEX idx_analytics_job_families_confidence ON analytics_job_families(cluster_confidence);",
            
            "CREATE INDEX idx_analytics_skill_bundles_cluster ON analytics_skill_bundles(cluster_id);",
            "CREATE INDEX idx_analytics_skill_bundles_specialized ON analytics_skill_bundles(is_specialized);",
            "CREATE INDEX idx_analytics_skill_bundles_confidence ON analytics_skill_bundles(bundle_confidence);",
            
            "CREATE INDEX idx_analytics_skill_demand_trends_category ON analytics_skill_demand_trends(velocity_category);",
            "CREATE INDEX idx_analytics_skill_demand_trends_direction ON analytics_skill_demand_trends(trend_direction);",
            "CREATE INDEX idx_analytics_skill_demand_trends_cagr_short ON analytics_skill_demand_trends(short_term_cagr);",
            "CREATE INDEX idx_analytics_skill_demand_trends_confidence ON analytics_skill_demand_trends(trend_confidence);",
            
            "CREATE INDEX idx_analytics_specialized_skills_category ON analytics_specialized_skills(specialization_category);",
            "CREATE INDEX idx_analytics_specialized_skills_importance ON analytics_specialized_skills(strategic_importance);",
            "CREATE INDEX idx_analytics_specialized_skills_lifecycle ON analytics_specialized_skills(skill_lifecycle_stage);",
            "CREATE INDEX idx_analytics_specialized_skills_prevalence ON analytics_specialized_skills(prevalence_percent);",
            
            "CREATE INDEX idx_analytics_bundle_characteristics_category ON analytics_bundle_characteristics(dominant_category);",
            "CREATE INDEX idx_analytics_bundle_characteristics_level ON analytics_bundle_characteristics(application_level);",
            "CREATE INDEX idx_analytics_bundle_characteristics_value ON analytics_bundle_characteristics(business_value_score);",
            "CREATE INDEX idx_analytics_bundle_characteristics_quality ON analytics_bundle_characteristics(silhouette_score);"
        ]
        
        for index_sql in indexes:
            try:
                conn.execute(index_sql)
                logger.debug(f"Created index: {index_sql.split()[2]}")  # Extract index name
            except sqlite3.Error as e:
                logger.warning(f"Could not create index: {e}")
    
    def _add_enhanced_schema_metadata(self, conn: sqlite3.Connection) -> None:
        """Add enhanced schema metadata with Phase 0 implementation status."""
        # Insert initial metadata records
        created_at = datetime.now().isoformat()
        
        # Get table counts from configuration
        tables_config = self.schema_config['tables']
        naming_config = self.schema_config['naming_convention']
        
        # Build metadata from configuration
        metadata = [
            ('schema_version', self.schema_version, 'schema', 'Enhanced database schema version'),
            ('table_count', str(tables_config['total_count']), 'stats', 'Total number of tables in enhanced schema'),
            ('core_tables_count', str(tables_config['core_data_count']), 'stats', 'Number of core data tables'),
            ('analytics_tables_count', str(tables_config['analytics_count']), 'stats', 'Number of analytics tables'),
            ('system_tables_count', str(tables_config['system_count']), 'stats', 'Number of system tables'),
            ('phase_status', 'Phase_0_Schema_Complete', 'version', 'Current implementation phase status'),
            ('phase0_populated_tables', '0', 'stats', 'Number of tables populated in Phase 0'),
            ('last_data_refresh', '', 'stats', 'Timestamp of last complete data refresh'),
            ('created_date', created_at, 'schema', 'When enhanced schema was created'),
            ('source_document', 'docs/ENHANCED_DATABASE_SCHEMA.md', 'schema', 'Source schema specification'),
            ('purpose', 'NAB Skills Intelligence Platform - Enhanced Analytics', 'schema', 'Database purpose'),
            ('naming_convention', f"{naming_config['core_prefix']}*, {naming_config['analytics_prefix']}*, {naming_config['system_prefix']}*", 'schema', 'Business-meaningful table naming')
        ]
        
        # Add any additional configured metadata
        for record in self.metadata_config.get('initial_records', []):
            key = record.get('key')
            # Skip if already added above
            if not any(meta[0] == key for meta in metadata):
                metadata.append((
                    key,
                    record.get('value', ''),
                    record.get('category', 'general'),
                    record.get('description', f'Metadata for {key}')
                ))
        
        conn.executemany(
            "INSERT OR REPLACE INTO sys_schema_metadata (metadata_key, metadata_value, metadata_category, description) VALUES (?, ?, ?, ?)",
            metadata
        )
        logger.debug("Added enhanced schema metadata")
    
    def check_schema_version(self) -> Optional[str]:
        """Check current schema version."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT metadata_value FROM sys_schema_metadata WHERE metadata_key = 'schema_version'"
                )
                result = cursor.fetchone()
                return result[0] if result else None
        except sqlite3.Error:
            return None
    
    def validate_schema(self) -> bool:
        """
        Validate that enhanced schema was created correctly.
        
        Returns:
            True if schema is valid
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check all required tables exist
                required_tables = [
                    # Core data tables (5)
                    'core_job_architecture', 'core_skills_taxonomy', 'core_job_skill_requirements',
                    'core_workforce_current', 'core_position_timeline',
                    # Analytics tables (10)
                    'analytics_movement_patterns', 'analytics_job_similarities', 'analytics_skill_rarity',
                    'analytics_job_defining_skills', 'analytics_job_families', 'analytics_skill_bundles',
                    'analytics_skill_demand_trends', 'analytics_specialized_skills', 'analytics_bundle_characteristics',
                    # System tables (1)
                    'sys_schema_metadata'
                ]
                
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                )
                existing_tables = [row[0] for row in cursor.fetchall()]
                
                missing_tables = set(required_tables) - set(existing_tables)
                if missing_tables:
                    logger.error(f"Missing tables: {missing_tables}")
                    return False
                
                # Check foreign key constraints are enabled
                cursor = conn.execute("PRAGMA foreign_keys;")
                fk_enabled = cursor.fetchone()[0]
                if not fk_enabled:
                    logger.warning("Foreign key constraints not enabled")
                
                # Validate table count matches expected
                table_count = len(existing_tables)
                expected_count = self.schema_config.get('table_count', 15)
                if table_count != expected_count:
                    logger.warning(f"Table count mismatch: expected {expected_count}, found {table_count}")
                
                logger.info(f"Enhanced schema validation passed: {table_count} tables created")
                return True
                
        except Exception as e:
            logger.error(f"Schema validation failed: {e}")
            return False
    
    def get_table_info(self) -> dict:
        """
        Get information about created tables.
        
        Returns:
            Dictionary with table names and row counts
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                tables_info = {}
                
                # Get all table names
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                )
                table_names = [row[0] for row in cursor.fetchall()]
                
                # Get row count for each table
                for table in table_names:
                    try:
                        cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                        row_count = cursor.fetchone()[0]
                        tables_info[table] = row_count
                    except sqlite3.Error:
                        tables_info[table] = "Error counting rows"
                
                return tables_info
                
        except Exception as e:
            logger.error(f"Failed to get table info: {e}")
            return {} 
    
    def update_phase_status(self, phase_status: str, populated_tables_count: int = 0) -> None:
        """Update the phase status and populated tables count in metadata."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                updated_at = datetime.now().isoformat()
                
                # Update phase status
                conn.execute(
                    "UPDATE sys_schema_metadata SET metadata_value = ?, updated_timestamp = ? WHERE metadata_key = 'phase_status'",
                    (phase_status, updated_at)
                )
                
                # Update populated tables count
                conn.execute(
                    "UPDATE sys_schema_metadata SET metadata_value = ?, updated_timestamp = ? WHERE metadata_key = 'phase0_populated_tables'",
                    (str(populated_tables_count), updated_at)
                )
                
                # Update last data refresh timestamp
                conn.execute(
                    "UPDATE sys_schema_metadata SET metadata_value = ?, updated_timestamp = ? WHERE metadata_key = 'last_data_refresh'",
                    (updated_at, updated_at)
                )
                
                conn.commit()
                logger.debug(f"Updated phase status to: {phase_status}")
                
        except Exception as e:
            logger.error(f"Failed to update phase status: {e}")
    
    def _get_fallback_schema_config(self) -> dict:
        """Provide fallback schema configuration if not available from config files."""
        return {
            'version': '2.0',
            'tables': {
                'total_count': 15,
                'core_data_count': 5,
                'analytics_count': 10,
                'system_count': 1
            },
            'phases': {
                'phase_0': {
                    'populated_tables': 6,
                    'description': 'Foundation data with core tables and movement analytics'
                }
            },
            'naming_convention': {
                'core_prefix': 'core_',
                'analytics_prefix': 'analytics_',
                'system_prefix': 'sys_'
            },
            'core_tables': {
                'core_job_architecture': {'description': 'Job framework and organisational taxonomy'},
                'core_skills_taxonomy': {'description': 'Skills classification and taxonomy system'},
                'core_job_skill_requirements': {'description': 'Job-skill relationship matrix'},
                'core_workforce_current': {'description': 'Current workforce snapshot'},
                'core_position_timeline': {'description': 'Historical position data'}
            },
            'analytics_tables': {
                'phase_0': {
                    'analytics_movement_patterns': {'description': 'Aggregated movement patterns'}
                },
                'phase_1': {
                    'analytics_job_similarities': {'description': 'Enhanced job similarities'},
                    'analytics_skill_rarity': {'description': 'Complete skill rarity analysis'},
                    'analytics_job_defining_skills': {'description': 'Job-specific defining skills'}
                },
                'phase_3': {
                    'analytics_job_families': {'description': 'Job cluster assignments'},
                    'analytics_skill_bundles': {'description': 'Skills clustering'},
                    'analytics_skill_demand_trends': {'description': 'Multi-timeframe skill velocity'},
                    'analytics_specialized_skills': {'description': 'Individual specialized skills'},
                    'analytics_bundle_characteristics': {'description': 'Skill bundle characteristics'}
                }
            },
            'system_tables': {
                'sys_schema_metadata': {'description': 'System metadata and versioning'}
            },
            'metadata': {
                'initial_records': [
                    {'key': 'schema_version', 'value': '2.0', 'category': 'schema', 'description': 'Enhanced database schema version'},
                    {'key': 'table_count', 'value': '15', 'category': 'stats', 'description': 'Total number of tables in enhanced schema'},
                    {'key': 'purpose', 'value': 'NAB Skills Intelligence Platform - Enhanced Analytics', 'category': 'schema', 'description': 'Database purpose'}
                ]
            }
        }
    
    def _load_table_configurations(self) -> dict:
        """Load table configurations from schema config."""
        table_configs = {}
        
        # Load core tables
        core_tables = self.schema_config.get('core_tables', {})
        table_configs.update(core_tables)
        
        # Load analytics tables (all phases)
        analytics_tables = self.schema_config.get('analytics_tables', {})
        for phase, tables in analytics_tables.items():
            table_configs.update(tables)
        
        # Load system tables
        system_tables = self.schema_config.get('system_tables', {})
        table_configs.update(system_tables)
        
        return table_configs 
